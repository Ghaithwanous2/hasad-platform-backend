"""Hasad operations models: delivery tasks, custody handovers, and assignments.

The model follows the approved Hasad scenarios:

Direct delivery:
    FARMER_TO_DRIVER -> DRIVER_TO_TRADER

Delivery through a warehouse:
    FARMER_TO_DRIVER -> DRIVER_TO_WAREHOUSE
    -> WAREHOUSE_TO_DRIVER or WAREHOUSE_TO_TRADER

Every physical custody transfer has a neutral-inspector assignment. The
inspector documents facts and evidence; the warehouse performs warehouse
operations; the Quality Manager decides disputes.

The real Order, ShipmentBatch, DeliveryCompany, Warehouse, DriverProfile, and
Vehicle models will replace the temporary reference fields as those modules
are implemented. No historical handover/report is deleted or overwritten.
"""

from __future__ import annotations

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class DeliveryTask(models.Model):
    """A transport leg associated with one traceable shipment batch."""

    class FulfillmentType(models.TextChoices):
        DIRECT_DELIVERY = "DIRECT_DELIVERY", "توصيل مباشر إلى التاجر"
        WAREHOUSE_DELIVERY = "WAREHOUSE_DELIVERY", "توصيل عبر المستودع"

    class Status(models.TextChoices):
        PLANNED = "PLANNED", "مخططة"
        ACCEPTED = "ACCEPTED", "مقبولة من شركة التوصيل"
        DRIVER_ASSIGNED = "DRIVER_ASSIGNED", "تم تعيين السائق والمركبة"
        READY_FOR_PICKUP = "READY_FOR_PICKUP", "جاهزة للتحميل"
        IN_TRANSIT = "IN_TRANSIT", "قيد النقل"
        ARRIVED = "ARRIVED", "وصلت إلى النقطة التالية"
        COMPLETED = "COMPLETED", "مكتملة"
        CANCELLED = "CANCELLED", "ملغاة"

    task_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    reference_code = models.CharField(max_length=40, unique=True)

    # Temporary references until the dedicated modules are implemented.
    order_reference = models.CharField(max_length=80)
    batch_reference = models.CharField(max_length=80)
    delivery_company_name = models.CharField(max_length=160)
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="delivery_tasks_as_driver",
        null=True,
        blank=True,
    )
    managed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="delivery_tasks_managed",
    )

    fulfillment_type = models.CharField(
        max_length=30,
        choices=FulfillmentType.choices,
    )
    pickup_address = models.TextField()
    pickup_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    pickup_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    destination_address = models.TextField()
    destination_latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    destination_longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    scheduled_pickup_at = models.DateTimeField(null=True, blank=True)
    scheduled_delivery_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PLANNED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "مهمة توصيل"
        verbose_name_plural = "مهام التوصيل"
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["fulfillment_type", "status"]),
        ]

    def __str__(self):
        return self.reference_code

    def clean(self):
        errors = {}
        if self.managed_by_id and getattr(self.managed_by, "role", None) != "DELIVERY_MANAGER":
            errors["managed_by"] = "مدير المهمة يجب أن يكون من دور مدير التوصيل."
        if self.driver_id and getattr(self.driver, "role", None) != "DRIVER":
            errors["driver"] = "المستخدم المسند يجب أن يكون من دور السائق."
        if errors:
            raise ValidationError(errors)


class Handover(models.Model):
    """One physical custody transfer in the batch timeline.

    A handover is defined by the actual parties transferring custody, not by a
    generic label such as "receiving". This is what supports both direct and
    warehouse-based delivery accurately.
    """

    class Type(models.TextChoices):
        FARMER_TO_DRIVER = "FARMER_TO_DRIVER", "من المزارع إلى السائق"
        FARMER_TO_TRADER = "FARMER_TO_TRADER", "من المزارع إلى التاجر"
        DRIVER_TO_WAREHOUSE = "DRIVER_TO_WAREHOUSE", "من السائق إلى المستودع"
        WAREHOUSE_TO_DRIVER = "WAREHOUSE_TO_DRIVER", "من المستودع إلى السائق"
        WAREHOUSE_TO_TRADER = "WAREHOUSE_TO_TRADER", "من المستودع إلى التاجر"
        DRIVER_TO_TRADER = "DRIVER_TO_TRADER", "من السائق إلى التاجر"

    class Status(models.TextChoices):
        AWAITING_INSPECTOR = "AWAITING_INSPECTOR", "بانتظار إسناد المراقب"
        INSPECTOR_ASSIGNED = "INSPECTOR_ASSIGNED", "تم إسناد المراقب"
        INSPECTOR_ACCEPTED = "INSPECTOR_ACCEPTED", "قبل المراقب المهمة"
        IN_PROGRESS = "IN_PROGRESS", "قيد التوثيق"
        REPORT_SUBMITTED = "REPORT_SUBMITTED", "تم إرسال التقرير"
        COMPLETED = "COMPLETED", "مكتملة"
        CANCELLED = "CANCELLED", "ملغاة"

    class PartyType(models.TextChoices):
        FARMER = "FARMER", "المزارع"
        TRADER = "TRADER", "التاجر"
        DRIVER = "DRIVER", "السائق"
        WAREHOUSE = "WAREHOUSE", "المستودع"

    handover_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    delivery_task = models.ForeignKey(
        DeliveryTask,
        on_delete=models.PROTECT,
        related_name="handovers",
        null=True,
        blank=True,
    )
    # Temporary reference until ShipmentBatch is implemented.
    batch_reference = models.CharField(max_length=80)
    point_type = models.CharField(
        max_length=30,
        choices=Type.choices,
    )
    sequence = models.PositiveSmallIntegerField()

    # Generic party references are temporary until Farmer, Trader, Driver, and
    # Warehouse profiles are implemented. The party type remains explicit.
    from_party_type = models.CharField(max_length=30, choices=PartyType.choices)
    from_party_id = models.UUIDField(null=True, blank=True)
    to_party_type = models.CharField(max_length=30, choices=PartyType.choices)
    to_party_id = models.UUIDField(null=True, blank=True)

    location_address = models.TextField()
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
    )
    scheduled_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.AWAITING_INSPECTOR,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["delivery_task", "sequence", "created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["delivery_task", "sequence"],
                name="unique_handover_sequence_per_delivery_task",
            ),
        ]
        indexes = [
            models.Index(fields=["point_type", "status"]),
            models.Index(fields=["from_party_type", "to_party_type"]),
        ]
        verbose_name = "انتقال حيازة"
        verbose_name_plural = "انتقالات الحيازة"

    def __str__(self):
        task = self.delivery_task.reference_code if self.delivery_task_id else "بدون مهمة"
        return f"{task} - {self.sequence} - {self.point_type}"

    def clean(self):
        expected_parties = {
            self.Type.FARMER_TO_DRIVER: (
                self.PartyType.FARMER,
                self.PartyType.DRIVER,
            ),
            self.Type.FARMER_TO_TRADER: (
                self.PartyType.FARMER,
                self.PartyType.TRADER,
            ),
            self.Type.DRIVER_TO_WAREHOUSE: (
                self.PartyType.DRIVER,
                self.PartyType.WAREHOUSE,
            ),
            self.Type.WAREHOUSE_TO_DRIVER: (
                self.PartyType.WAREHOUSE,
                self.PartyType.DRIVER,
            ),
            self.Type.WAREHOUSE_TO_TRADER: (
                self.PartyType.WAREHOUSE,
                self.PartyType.TRADER,
            ),
            self.Type.DRIVER_TO_TRADER: (
                self.PartyType.DRIVER,
                self.PartyType.TRADER,
            ),
        }
        expected = expected_parties.get(self.point_type)
        if expected and (
            self.from_party_type != expected[0]
            or self.to_party_type != expected[1]
        ):
            raise ValidationError(
                {
                    "point_type": (
                        "نوع انتقال الحيازة لا يتوافق مع نوع الطرف المرسل "
                        "ونوع الطرف المستلم."
                    )
                }
            )

        # Direct farmer-to-trader pickup may have no delivery-company task.
        # All transfers involving a driver or warehouse must belong to a task.
        if (
            self.point_type != self.Type.FARMER_TO_TRADER
            and not self.delivery_task_id
        ):
            raise ValidationError(
                {"delivery_task": "انتقال الحيازة يجب أن يرتبط بمهمة توصيل."}
            )


class InspectorAssignment(models.Model):
    """Auditable assignment of one neutral inspector to one handover."""

    class Status(models.TextChoices):
        ASSIGNED = "ASSIGNED", "مسندة"
        ACCEPTED = "ACCEPTED", "مقبولة"
        REJECTED = "REJECTED", "مرفوضة بسبب تعارض أو تعذر"
        IN_PROGRESS = "IN_PROGRESS", "قيد التنفيذ"
        REPORT_SUBMITTED = "REPORT_SUBMITTED", "تم إرسال التقرير"
        EXPIRED = "EXPIRED", "منتهية"
        REASSIGNMENT_REQUIRED = "REASSIGNMENT_REQUIRED", "تحتاج إعادة إسناد"
        CANCELLED = "CANCELLED", "ملغاة"

    assignment_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    handover = models.ForeignKey(
        Handover,
        on_delete=models.PROTECT,
        related_name="inspector_assignments",
    )
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inspector_assignments",
    )
    assigned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="inspector_assignments_created",
    )
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.ASSIGNED,
    )
    is_current = models.BooleanField(default=True)
    rejection_reason = models.TextField(blank=True)
    exception_reason = models.TextField(blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    report_submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-assigned_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["handover"],
                condition=Q(is_current=True),
                name="one_current_inspector_per_handover",
            ),
        ]
        indexes = [
            models.Index(fields=["inspector", "status"]),
            models.Index(fields=["handover", "is_current"]),
        ]
        verbose_name = "إسناد مراقب محايد"
        verbose_name_plural = "إسنادات المراقبين المحايدين"

    def __str__(self):
        return f"{self.handover} -> {self.inspector}"

    def clean(self):
        errors = {}
        if self.inspector_id and getattr(self.inspector, "role", None) != "INSPECTOR":
            errors["inspector"] = "المستخدم المختار يجب أن يكون مراقباً محايداً."
        if self.assigned_by_id and getattr(self.assigned_by, "role", None) != "ADMIN":
            errors["assigned_by"] = "الإسناد النهائي يجب أن ينفذه مدير النظام."
        if (
            self.handover_id
            and self.handover.delivery_task_id
            and self.handover.delivery_task.driver_id == self.inspector_id
        ):
            errors["inspector"] = (
                "لا يجوز أن يكون سائق مهمة التوصيل هو مراقب نقطة الحيازة نفسها."
            )
        if self.is_current and self.status in {
            self.Status.REJECTED,
            self.Status.EXPIRED,
            self.Status.CANCELLED,
            self.Status.REASSIGNMENT_REQUIRED,
        }:
            errors["is_current"] = "الإسناد غير الفعال لا يمكن أن يبقى حالياً."
        if errors:
            raise ValidationError(errors)
