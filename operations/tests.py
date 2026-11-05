from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .models import DeliveryTask, Handover, InspectorAssignment


User = get_user_model()


class OperationsModelTestCase(TestCase):
    """Tests for the current temporary operations models.

    These tests verify model rules only. Geographical matching, availability,
    conflict-of-interest checks, and API permissions belong to the service/API
    test layers that will be added next.
    """

    def make_user(self, email, role):
        return User.objects.create_user(
            email=email,
            password="StrongPassword123!",
            role=role,
            is_active=True,
        )

    def setUp(self):
        self.admin = self.make_user("admin.operations@test.com", "ADMIN")
        self.delivery_manager = self.make_user(
            "delivery.manager@test.com",
            "DELIVERY_MANAGER",
        )
        self.driver = self.make_user("driver.operations@test.com", "DRIVER")
        self.other_driver = self.make_user("driver.other@test.com", "DRIVER")
        self.inspector_one = self.make_user(
            "inspector.one@test.com",
            "INSPECTOR",
        )
        self.inspector_two = self.make_user(
            "inspector.two@test.com",
            "INSPECTOR",
        )
        self.farmer = self.make_user("farmer.operations@test.com", "FARMER")
        self.trader = self.make_user("trader.operations@test.com", "TRADER")
        self.warehouse_user = self.make_user(
            "warehouse.operations@test.com",
            "WAREHOUSE_STAFF",
        )

    def make_delivery_task(self, *, driver=None, managed_by=None):
        task = DeliveryTask(
            reference_code="TASK-001",
            order_reference="ORDER-001",
            batch_reference="BATCH-001",
            delivery_company_name="Hasad Delivery",
            driver=driver or self.driver,
            managed_by=managed_by or self.delivery_manager,
            fulfillment_type=DeliveryTask.FulfillmentType.DIRECT_DELIVERY,
            pickup_address="مزرعة حمص",
            destination_address="تاجر دمشق",
        )
        task.full_clean()
        task.save()
        return task

    def make_handover(
        self,
        *,
        point_type,
        sequence=1,
        delivery_task=None,
        from_party_type=None,
        to_party_type=None,
    ):
        party_map = {
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
        expected_from, expected_to = party_map[point_type]
        handover = Handover(
            delivery_task=delivery_task,
            batch_reference="BATCH-001",
            point_type=point_type,
            sequence=sequence,
            from_party_type=from_party_type or expected_from,
            to_party_type=to_party_type or expected_to,
            location_address="نقطة العملية",
        )
        handover.full_clean()
        handover.save()
        return handover

    def test_delivery_task_accepts_valid_manager_and_driver(self):
        task = self.make_delivery_task()
        self.assertEqual(task.managed_by.role, "DELIVERY_MANAGER")
        self.assertEqual(task.driver.role, "DRIVER")

    def test_delivery_task_rejects_non_delivery_manager(self):
        task = DeliveryTask(
            reference_code="TASK-INVALID-MANAGER",
            order_reference="ORDER-001",
            batch_reference="BATCH-001",
            delivery_company_name="Hasad Delivery",
            driver=self.driver,
            managed_by=self.admin,
            fulfillment_type=DeliveryTask.FulfillmentType.DIRECT_DELIVERY,
            pickup_address="مزرعة حمص",
            destination_address="تاجر دمشق",
        )
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_delivery_task_rejects_non_driver(self):
        task = DeliveryTask(
            reference_code="TASK-INVALID-DRIVER",
            order_reference="ORDER-001",
            batch_reference="BATCH-001",
            delivery_company_name="Hasad Delivery",
            driver=self.trader,
            managed_by=self.delivery_manager,
            fulfillment_type=DeliveryTask.FulfillmentType.DIRECT_DELIVERY,
            pickup_address="مزرعة حمص",
            destination_address="تاجر دمشق",
        )
        with self.assertRaises(ValidationError):
            task.full_clean()

    def test_direct_farmer_to_trader_handover_does_not_need_delivery_task(self):
        handover = self.make_handover(
            point_type=Handover.Type.FARMER_TO_TRADER,
        )
        self.assertIsNone(handover.delivery_task)

    def test_all_supported_handover_types_accept_matching_parties(self):
        task = self.make_delivery_task()
        types = [
            Handover.Type.FARMER_TO_DRIVER,
            Handover.Type.DRIVER_TO_WAREHOUSE,
            Handover.Type.WAREHOUSE_TO_DRIVER,
            Handover.Type.WAREHOUSE_TO_TRADER,
            Handover.Type.DRIVER_TO_TRADER,
        ]
        for sequence, point_type in enumerate(types, start=1):
            handover = self.make_handover(
                point_type=point_type,
                sequence=sequence,
                delivery_task=task,
            )
            self.assertEqual(handover.point_type, point_type)

    def test_handover_rejects_wrong_party_direction(self):
        task = self.make_delivery_task()
        handover = Handover(
            delivery_task=task,
            batch_reference="BATCH-001",
            point_type=Handover.Type.DRIVER_TO_WAREHOUSE,
            sequence=1,
            from_party_type=Handover.PartyType.FARMER,
            to_party_type=Handover.PartyType.WAREHOUSE,
            location_address="مستودع حمص",
        )
        with self.assertRaises(ValidationError):
            handover.full_clean()

    def test_handover_requires_delivery_task_when_driver_or_warehouse_is_involved(self):
        handover = Handover(
            batch_reference="BATCH-001",
            point_type=Handover.Type.DRIVER_TO_WAREHOUSE,
            sequence=1,
            from_party_type=Handover.PartyType.DRIVER,
            to_party_type=Handover.PartyType.WAREHOUSE,
            location_address="مستودع حمص",
        )
        with self.assertRaises(ValidationError):
            handover.full_clean()

    def test_inspector_assignment_accepts_inspector_and_admin(self):
        task = self.make_delivery_task()
        handover = self.make_handover(
            point_type=Handover.Type.FARMER_TO_DRIVER,
            delivery_task=task,
        )
        assignment = InspectorAssignment(
            handover=handover,
            inspector=self.inspector_one,
            assigned_by=self.admin,
        )
        assignment.full_clean()
        assignment.save()
        self.assertTrue(assignment.is_current)

    def test_inspector_assignment_rejects_non_inspector(self):
        task = self.make_delivery_task()
        handover = self.make_handover(
            point_type=Handover.Type.FARMER_TO_DRIVER,
            delivery_task=task,
        )
        assignment = InspectorAssignment(
            handover=handover,
            inspector=self.driver,
            assigned_by=self.admin,
        )
        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_inspector_assignment_rejects_non_admin_assigner(self):
        task = self.make_delivery_task()
        handover = self.make_handover(
            point_type=Handover.Type.FARMER_TO_DRIVER,
            delivery_task=task,
        )
        assignment = InspectorAssignment(
            handover=handover,
            inspector=self.inspector_one,
            assigned_by=self.delivery_manager,
        )
        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_driver_cannot_be_assigned_as_inspector_for_same_task(self):
        task = self.make_delivery_task()
        handover = self.make_handover(
            point_type=Handover.Type.FARMER_TO_DRIVER,
            delivery_task=task,
        )
        assignment = InspectorAssignment(
            handover=handover,
            inspector=self.driver,
            assigned_by=self.admin,
        )
        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_two_different_inspectors_can_cover_two_handovers(self):
        task = self.make_delivery_task()
        pickup = self.make_handover(
            point_type=Handover.Type.FARMER_TO_DRIVER,
            sequence=1,
            delivery_task=task,
        )
        receiving = self.make_handover(
            point_type=Handover.Type.DRIVER_TO_TRADER,
            sequence=2,
            delivery_task=task,
        )
        first = InspectorAssignment(
            handover=pickup,
            inspector=self.inspector_one,
            assigned_by=self.admin,
        )
        second = InspectorAssignment(
            handover=receiving,
            inspector=self.inspector_two,
            assigned_by=self.admin,
        )
        first.full_clean()
        second.full_clean()
        first.save()
        second.save()
        self.assertEqual(
            InspectorAssignment.objects.filter(is_current=True).count(),
            2,
        )

    def test_database_rejects_two_current_assignments_for_same_handover(self):
        task = self.make_delivery_task()
        handover = self.make_handover(
            point_type=Handover.Type.FARMER_TO_DRIVER,
            delivery_task=task,
        )
        first = InspectorAssignment.objects.create(
            handover=handover,
            inspector=self.inspector_one,
            assigned_by=self.admin,
        )
        self.assertTrue(first.is_current)
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                InspectorAssignment.objects.create(
                    handover=handover,
                    inspector=self.inspector_two,
                    assigned_by=self.admin,
                )
