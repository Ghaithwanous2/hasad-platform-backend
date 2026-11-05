from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permission_classes import (
    HasAnyConfiguredPermission,
    HasConfiguredPermission,
)

from .models import DeliveryTask, Handover
from .serializers import (
    AssignInspectorSerializer,
    CreateHandoverSerializer,
    HandoverSerializer,
    InspectorAssignmentSerializer,
)
from .services.handover import HandoverCreationError, create_handover
from .services.inspector_assignment import (
    InspectorAssignmentError,
    assign_inspector,
)


class CreateHandoverView(APIView):
    permission_classes = [
        IsAuthenticated,
        HasAnyConfiguredPermission,
    ]
    permission_names = {
        "handover.create_system",
        "handover.create_farmer_origin",
        "handover.create_trader_destination",
        "handover.create_warehouse_point",
    }

    @extend_schema(
        request=CreateHandoverSerializer,
        responses={
            201: HandoverSerializer,
            400: OpenApiResponse(description="بيانات الانتقال غير صالحة."),
            403: OpenApiResponse(description="لا يملك المستخدم الصلاحية."),
            404: OpenApiResponse(description="مهمة التوصيل غير موجودة."),
        },
        tags=["Handovers"],
        summary="إنشاء نقطة انتقال حيازة",
        description=(
            "ينشئ انتقال حيازة واحداً. ينشئ كل طرف النقطة الموجودة في موقعه، "
            "ثم يتم إسناد المراقب المحايد بعملية منفصلة."
        ),
    )
    def post(self, request):
        input_serializer = CreateHandoverSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        data = input_serializer.validated_data.copy()

        delivery_task = None
        delivery_task_id = data.pop("delivery_task_id", None)
        if delivery_task_id:
            delivery_task = get_object_or_404(
                DeliveryTask,
                task_id=delivery_task_id,
            )

        try:
            handover = create_handover(
                created_by=request.user,
                delivery_task=delivery_task,
                **data,
            )
        except HandoverCreationError as exc:
            detail = (
                exc.message_dict
                if hasattr(exc, "message_dict")
                else exc.messages
            )
            return Response(
                {"detail": detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            HandoverSerializer(handover).data,
            status=status.HTTP_201_CREATED,
        )


class AssignHandoverInspectorView(APIView):
    """Assign one neutral inspector to one custody-transfer point."""

    permission_classes = [
        IsAuthenticated,
        HasConfiguredPermission,
    ]
    permission_name = "handover.assign_neutral_inspector"

    @extend_schema(
        request=AssignInspectorSerializer,
        responses={
            201: InspectorAssignmentSerializer,
            400: OpenApiResponse(description="بيانات الإسناد غير صالحة."),
            403: OpenApiResponse(description="لا يملك المستخدم الصلاحية."),
            404: OpenApiResponse(description="نقطة الانتقال غير موجودة."),
        },
        tags=["Handovers"],
        summary="إسناد مراقب محايد لنقطة انتقال",
        description=(
            "ينفذ ADMIN الإسناد النهائي لمراقب INSPECTOR إلى انتقال حيازة "
            "محدد، وليس إلى مهمة التوصيل كاملة."
        ),
    )
    def post(self, request, handover_id):
        handover = get_object_or_404(
            Handover,
            handover_id=handover_id,
        )

        input_serializer = AssignInspectorSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        try:
            result = assign_inspector(
                handover=handover,
                inspector=input_serializer.validated_data["inspector"],
                assigned_by=request.user,
                exception_reason=input_serializer.validated_data.get(
                    "exception_reason",
                    "",
                ),
            )
        except InspectorAssignmentError as exc:
            detail = (
                exc.message_dict
                if hasattr(exc, "message_dict")
                else exc.messages
            )
            return Response(
                {"detail": detail},
                status=status.HTTP_400_BAD_REQUEST,
            )

        output_serializer = InspectorAssignmentSerializer(result.assignment)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
        )
