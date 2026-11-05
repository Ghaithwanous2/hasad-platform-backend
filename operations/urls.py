from django.urls import path

from .views import AssignHandoverInspectorView, CreateHandoverView


urlpatterns = [
    path(
        "handovers/create/",
        CreateHandoverView.as_view(),
        name="handover-create",
    ),
    path(
        "handovers/<uuid:handover_id>/assign-inspector/",
        AssignHandoverInspectorView.as_view(),
        name="handover-assign-inspector",
    ),
]
