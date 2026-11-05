"""Business service for creating custody-transfer handovers."""

from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from ..models import Handover


class HandoverCreationError(ValidationError):
    """Raised when a handover violates the custody workflow."""


@transaction.atomic
def create_handover(
    *,
    created_by,
    point_type: str,
    sequence: int,
    batch_reference: str,
    delivery_task=None,
    from_party_type: str,
    from_party_id=None,
    to_party_type: str,
    to_party_id=None,
    location_address: str,
    latitude=None,
    longitude=None,
    scheduled_at=None,
) -> Handover:
    """Create one physical custody-transfer point.

    Each physical location that contains a custody transfer gets its own
    Handover. The creator may create only the point belonging to their role:

    - FARMER: FARMER_TO_DRIVER or FARMER_TO_TRADER, starting from that farmer.
    - TRADER: DRIVER_TO_TRADER, ending at that trader.
    - WAREHOUSE_MANAGER/STAFF: a warehouse-related handover for their flow.
    - Internal roles: may create a contextual system handover.

    This function creates the handover only. Assigning the neutral inspector
    is a separate auditable operation.
    """
    if created_by is None:
        raise HandoverCreationError(
            {"created_by": "منشئ نقطة الانتقال مطلوب."}
        )

    if not batch_reference or not batch_reference.strip():
        raise HandoverCreationError(
            {"batch_reference": "مرجع الدفعة مطلوب."}
        )

    if sequence < 1:
        raise HandoverCreationError(
            {"sequence": "يجب أن يبدأ ترتيب الانتقال من 1 أو أكثر."}
        )

    if not location_address or not location_address.strip():
        raise HandoverCreationError(
            {"location_address": "عنوان نقطة الانتقال مطلوب."}
        )

    creator_role = getattr(created_by, "role", None)
    creator_id = getattr(
        created_by,
        "account_id",
        getattr(created_by, "pk", None),
    )

    if creator_role == "FARMER":
        allowed_types = {
            Handover.Type.FARMER_TO_DRIVER,
            Handover.Type.FARMER_TO_TRADER,
        }
        if (
            point_type not in allowed_types
            or from_party_type != Handover.PartyType.FARMER
            or from_party_id != creator_id
        ):
            raise HandoverCreationError(
                {
                    "detail": (
                        "المزارع يستطيع إنشاء نقطة تبدأ منه فقط، "
                        "ويجب أن يكون from_party_id حسابه."
                    )
                }
            )

    elif creator_role == "TRADER":
        if (
            point_type != Handover.Type.DRIVER_TO_TRADER
            or to_party_type != Handover.PartyType.TRADER
            or to_party_id != creator_id
        ):
            raise HandoverCreationError(
                {
                    "detail": (
                        "التاجر يستطيع إنشاء نقطة DRIVER_TO_TRADER "
                        "التي تنتهي عنده فقط."
                    )
                }
            )

    elif creator_role in {"WAREHOUSE_MANAGER", "WAREHOUSE_STAFF"}:
        allowed_types = {
            Handover.Type.DRIVER_TO_WAREHOUSE,
            Handover.Type.WAREHOUSE_TO_DRIVER,
            Handover.Type.WAREHOUSE_TO_TRADER,
        }
        if point_type not in allowed_types:
            raise HandoverCreationError(
                {
                    "detail": (
                        "فريق المستودع يستطيع إنشاء نقاط المستودع فقط."
                    )
                }
            )

    elif creator_role not in {
        "ADMIN",
        "OPERATIONS_STAFF",
        "DELIVERY_MANAGER",
    }:
        raise HandoverCreationError(
            {"detail": "هذا الدور لا يملك صلاحية إنشاء نقطة انتقال."}
        )

    # A handover involving a driver belongs to a delivery task. Direct
    # farmer-to-trader and direct warehouse-to-trader pickup happen at one
    # physical location and therefore do not require a DeliveryTask.
    taskless_types = {
        Handover.Type.FARMER_TO_TRADER,
        Handover.Type.WAREHOUSE_TO_TRADER,
    }
    if point_type not in taskless_types and delivery_task is None:
        raise HandoverCreationError(
            {
                "delivery_task": (
                    "هذا النوع من الانتقال يتضمن سائقاً، "
                    "ولذلك يجب أن يرتبط بمهمة توصيل."
                )
            }
        )

    handover = Handover(
        delivery_task=delivery_task,
        batch_reference=batch_reference.strip(),
        point_type=point_type,
        sequence=sequence,
        from_party_type=from_party_type,
        from_party_id=from_party_id,
        to_party_type=to_party_type,
        to_party_id=to_party_id,
        location_address=location_address.strip(),
        latitude=latitude,
        longitude=longitude,
        scheduled_at=scheduled_at,
    )
    handover.full_clean()
    handover.save()
    return handover
