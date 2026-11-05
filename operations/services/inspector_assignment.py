
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import Handover, InspectorAssignment


class InspectorAssignmentError(ValidationError):
    """A business-rule error raised during inspector assignment."""


@dataclass(frozen=True)
class AssignmentResult:
    assignment: InspectorAssignment
    replaced_assignment: InspectorAssignment | None = None


def _role(user) -> str | None:
    return getattr(user, "role", None)


def _is_active(user) -> bool:
    return bool(getattr(user, "is_active", False))


def _same_delivery_inspector_exists(*, handover: Handover, inspector) -> bool:

    task_id = handover.delivery_task_id
    if not task_id:
        return False

    return InspectorAssignment.objects.filter(
        handover__delivery_task_id=task_id,
        inspector_id=inspector.pk,
        is_current=True,
    ).exclude(handover_id=handover.pk).exists()


def _validate_assignment_request(
    *,
    handover: Handover,
    inspector,
    assigned_by,
    exception_reason: str,
) -> None:
    if not getattr(handover, "pk", None):
        raise InspectorAssignmentError(
            {"handover": "يجب حفظ نقطة الانتقال قبل إسناد المراقب."}
        )

    if _role(assigned_by) != "ADMIN":
        raise InspectorAssignmentError(
            {"assigned_by": "الإسناد النهائي للمراقب ينفذه ADMIN فقط."}
        )

    if _role(inspector) != "INSPECTOR":
        raise InspectorAssignmentError(
            {"inspector": "المستخدم المختار يجب أن يكون مراقباً محايداً."}
        )

    if not _is_active(inspector):
        raise InspectorAssignmentError(
            {"inspector": "لا يمكن إسناد مهمة إلى حساب مراقب غير فعال."}
        )

    if _same_delivery_inspector_exists(
        handover=handover,
        inspector=inspector,
    ) and not exception_reason.strip():
        raise InspectorAssignmentError(
            {
                "exception_reason": (
                    "المراقب مستخدم في نقطة أخرى من المهمة. "
                    "يجب تقديم سبب استثناء موثق من ADMIN."
                )
            }
        )


def assign_inspector(
    *,
    handover: Handover,
    inspector,
    assigned_by,
    exception_reason: str = "",
    replace_current: bool = False,
) -> AssignmentResult:

    exception_reason = exception_reason.strip()

    with transaction.atomic():
        locked_handover = Handover.objects.select_for_update().get(
            pk=handover.pk
        )
        _validate_assignment_request(
            handover=locked_handover,
            inspector=inspector,
            assigned_by=assigned_by,
            exception_reason=exception_reason,
        )

        current = InspectorAssignment.objects.select_for_update().filter(
            handover=locked_handover,
            is_current=True,
        ).first()

        if current and not replace_current:
            raise InspectorAssignmentError(
                {
                    "handover": (
                        "نقطة الانتقال لديها مراقب حالي. "
                        "استخدم إعادة الإسناد بشكل صريح."
                    )
                }
            )

        if current:
            current.is_current = False
            current.status = InspectorAssignment.Status.REASSIGNMENT_REQUIRED
            current.save(update_fields=["is_current", "status"])

        assignment = InspectorAssignment(
            handover=locked_handover,
            inspector=inspector,
            assigned_by=assigned_by,
            status=InspectorAssignment.Status.ASSIGNED,
            is_current=True,
            exception_reason=exception_reason,
        )
        assignment.full_clean()
        assignment.save()

        locked_handover.status = Handover.Status.INSPECTOR_ASSIGNED
        locked_handover.save(update_fields=["status", "updated_at"])

        return AssignmentResult(
            assignment=assignment,
            replaced_assignment=current,
        )


def reassign_inspector(
    *,
    handover: Handover,
    inspector,
    assigned_by,
    exception_reason: str = "",
) -> AssignmentResult:
    """Explicitly replace the current assignment without deleting history."""
    return assign_inspector(
        handover=handover,
        inspector=inspector,
        assigned_by=assigned_by,
        exception_reason=exception_reason,
        replace_current=True,
    )


def assign_inspector_from_candidates(
    *,
    handover: Handover,
    candidates: Iterable,
    assigned_by,
    selector: Callable[[list], object],
    exception_reason: str = "",
) -> AssignmentResult:
    """Select and assign a candidate using an injected policy.

    The selector will later sort candidates by geographic distance and
    availability. Keeping it injected now prevents fake location logic from
    entering the domain model before InspectorProfile exists.
    """
    eligible = [
        candidate
        for candidate in candidates
        if _role(candidate) == "INSPECTOR"
        and _is_active(candidate)
    ]
    if not eligible:
        raise InspectorAssignmentError(
            {"inspector": "لا يوجد مراقب فعال مؤهل ضمن المرشحين."}
        )

    selected = selector(eligible)
    if selected not in eligible:
        raise InspectorAssignmentError(
            {"inspector": "اختار المرشح المحدد خارج قائمة المرشحين المؤهلين."}
        )

    return assign_inspector(
        handover=handover,
        inspector=selected,
        assigned_by=assigned_by,
        exception_reason=exception_reason,
    )
