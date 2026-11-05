from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Handover, InspectorAssignment


User = get_user_model()


class CreateHandoverSerializer(serializers.Serializer):
    point_type = serializers.ChoiceField(choices=Handover.Type.choices)
    sequence = serializers.IntegerField(min_value=1)
    batch_reference = serializers.CharField(max_length=80)
    delivery_task_id = serializers.UUIDField(required=False, allow_null=True)
    from_party_type = serializers.ChoiceField(choices=Handover.PartyType.choices)
    from_party_id = serializers.UUIDField()
    to_party_type = serializers.ChoiceField(choices=Handover.PartyType.choices)
    to_party_id = serializers.UUIDField()
    location_address = serializers.CharField()
    latitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )
    longitude = serializers.DecimalField(
        max_digits=9,
        decimal_places=6,
        required=False,
        allow_null=True,
    )
    scheduled_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        expected_parties = {
            Handover.Type.FARMER_TO_DRIVER: (
                Handover.PartyType.FARMER,
                Handover.PartyType.DRIVER,
            ),
            Handover.Type.FARMER_TO_TRADER: (
                Handover.PartyType.FARMER,
                Handover.PartyType.TRADER,
            ),
            Handover.Type.DRIVER_TO_WAREHOUSE: (
                Handover.PartyType.DRIVER,
                Handover.PartyType.WAREHOUSE,
            ),
            Handover.Type.WAREHOUSE_TO_DRIVER: (
                Handover.PartyType.WAREHOUSE,
                Handover.PartyType.DRIVER,
            ),
            Handover.Type.WAREHOUSE_TO_TRADER: (
                Handover.PartyType.WAREHOUSE,
                Handover.PartyType.TRADER,
            ),
            Handover.Type.DRIVER_TO_TRADER: (
                Handover.PartyType.DRIVER,
                Handover.PartyType.TRADER,
            ),
        }

        point_type = attrs["point_type"]
        expected_from, expected_to = expected_parties[point_type]

        if attrs["from_party_type"] != expected_from:
            raise serializers.ValidationError(
                {
                    "from_party_type": (
                        f"هذا الانتقال يجب أن يبدأ من {expected_from}."
                    )
                }
            )

        if attrs["to_party_type"] != expected_to:
            raise serializers.ValidationError(
                {
                    "to_party_type": (
                        f"هذا الانتقال يجب أن ينتهي عند {expected_to}."
                    )
                }
            )

        taskless_types = {
            Handover.Type.FARMER_TO_TRADER,
            Handover.Type.WAREHOUSE_TO_TRADER,
        }
        has_delivery_task = bool(attrs.get("delivery_task_id"))

        if point_type in taskless_types and has_delivery_task:
            raise serializers.ValidationError(
                {
                    "delivery_task_id": (
                        "هذا استلام مباشر في موقع واحد، ولا يحتاج DeliveryTask."
                    )
                }
            )

        if point_type not in taskless_types and not has_delivery_task:
            raise serializers.ValidationError(
                {
                    "delivery_task_id": (
                        "هذا الانتقال يتضمن سائقاً، ويحتاج DeliveryTask."
                    )
                }
            )

        return attrs


class HandoverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Handover
        fields = (
            "handover_id",
            "delivery_task",
            "batch_reference",
            "point_type",
            "sequence",
            "from_party_type",
            "from_party_id",
            "to_party_type",
            "to_party_id",
            "location_address",
            "latitude",
            "longitude",
            "scheduled_at",
            "status",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "handover_id",
            "status",
            "created_at",
            "updated_at",
        )


class AssignInspectorSerializer(serializers.Serializer):
    inspector_id = serializers.PrimaryKeyRelatedField(
        source="inspector",
        queryset=User.objects.filter(
            role="INSPECTOR",
            is_active=True,
        ),
        help_text="UUID of the active INSPECTOR account.",
    )
    exception_reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text=(
            "Required when the same inspector is already assigned to another "
            "handover in this delivery."
        ),
    )


class InspectorAssignmentSerializer(serializers.ModelSerializer):
    inspector_id = serializers.UUIDField(
        source="inspector.account_id",
        read_only=True,
    )
    assigned_by_id = serializers.UUIDField(
        source="assigned_by.account_id",
        read_only=True,
    )
    handover_id = serializers.UUIDField(
        source="handover.handover_id",
        read_only=True,
    )

    class Meta:
        model = InspectorAssignment
        fields = (
            "assignment_id",
            "handover_id",
            "inspector_id",
            "assigned_by_id",
            "status",
            "is_current",
            "exception_reason",
            "assigned_at",
            "accepted_at",
            "report_submitted_at",
        )
        read_only_fields = fields
