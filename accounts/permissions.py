
from __future__ import annotations

from typing import Final


# ---------------------------------------------------------------------------
# Roles
# ---------------------------------------------------------------------------

ADMIN: Final = "ADMIN"
OPERATIONS_STAFF: Final = "OPERATIONS_STAFF"
QUALITY_MANAGER: Final = "QUALITY_MANAGER"
DELIVERY_MANAGER: Final = "DELIVERY_MANAGER"
WAREHOUSE_MANAGER: Final = "WAREHOUSE_MANAGER"
WAREHOUSE_STAFF: Final = "WAREHOUSE_STAFF"
AUDITOR: Final = "AUDITOR"
FARMER: Final = "FARMER"
TRADER: Final = "TRADER"
DRIVER: Final = "DRIVER"
INSPECTOR: Final = "INSPECTOR"

ALL_ROLES: Final[frozenset[str]] = frozenset(
    {
        ADMIN,
        OPERATIONS_STAFF,
        QUALITY_MANAGER,
        DELIVERY_MANAGER,
        WAREHOUSE_MANAGER,
        WAREHOUSE_STAFF,
        AUDITOR,
        FARMER,
        TRADER,
        DRIVER,
        INSPECTOR,
    }
)


# ---------------------------------------------------------------------------
# Scopes
# ---------------------------------------------------------------------------

GLOBAL: Final = "GLOBAL"
COMPANY: Final = "COMPANY"
WAREHOUSE: Final = "WAREHOUSE"
ASSIGNED_TASKS: Final = "ASSIGNED_TASKS"
ASSIGNED_HANDOVERS: Final = "ASSIGNED_HANDOVERS"
ASSIGNED_CASES: Final = "ASSIGNED_CASES"
OWN_RECORDS: Final = "OWN_RECORDS"
CONTEXTUAL: Final = "CONTEXTUAL"
PUBLIC_MARKET: Final = "PUBLIC_MARKET"


# ---------------------------------------------------------------------------
# Handover and inspection constants
# ---------------------------------------------------------------------------

HANDOVER_PICKUP: Final = "PICKUP"
HANDOVER_RECEIVING: Final = "RECEIVING"
HANDOVER_WAREHOUSE_RELEASE: Final = "WAREHOUSE_RELEASE"
HANDOVER_DISPUTE_INSPECTION: Final = "DISPUTE_INSPECTION"

HANDOVER_TYPES: Final[frozenset[str]] = frozenset(
    {
        HANDOVER_PICKUP,
        HANDOVER_RECEIVING,
        HANDOVER_WAREHOUSE_RELEASE,
        HANDOVER_DISPUTE_INSPECTION,
    }
)

INSPECTION_NOT_REQUIRED: Final = "NOT_REQUIRED"
INSPECTION_REQUESTED: Final = "REQUESTED"
INSPECTION_ASSIGNED: Final = "ASSIGNED"
INSPECTION_ACCEPTED: Final = "ACCEPTED"
INSPECTION_IN_PROGRESS: Final = "IN_PROGRESS"
INSPECTION_REPORT_SUBMITTED: Final = "REPORT_SUBMITTED"
INSPECTION_REVIEWED: Final = "REVIEWED"
INSPECTION_REJECTED: Final = "REJECTED"
INSPECTION_EXPIRED: Final = "EXPIRED"
INSPECTION_REASSIGNMENT_REQUIRED: Final = "REASSIGNMENT_REQUIRED"
INSPECTION_CANCELLED: Final = "CANCELLED"


# ---------------------------------------------------------------------------
# Permission dictionary
# ---------------------------------------------------------------------------
#
# Shape deliberately stays simple so it is easy to consume from DRF:
# {
#     "roles": {"ROLE_A", "ROLE_B"},
#     "scope": "SCOPE_NAME",
# }
#

PERMISSIONS: Final[dict[str, dict[str, object]]] = {
    # --------------------------- Users and access -------------------------
    "users.view": {"roles": {ADMIN, OPERATIONS_STAFF, AUDITOR}, "scope": GLOBAL},
    "users.view_sensitive": {"roles": {ADMIN}, "scope": GLOBAL},
    "users.create_staff_account": {"roles": {ADMIN}, "scope": GLOBAL},
    "users.create_admin_account": {"roles": {ADMIN}, "scope": GLOBAL},
    "users.assign_role": {"roles": {ADMIN}, "scope": GLOBAL},
    "users.activate": {"roles": {ADMIN, OPERATIONS_STAFF}, "scope": CONTEXTUAL},
    "users.deactivate": {"roles": {ADMIN}, "scope": GLOBAL},

    # --------------------------- Market and orders -------------------------
    "offers.view": {
        "roles": {ADMIN, OPERATIONS_STAFF, AUDITOR, FARMER, TRADER},
        "scope": CONTEXTUAL,
    },
    "offers.create": {"roles": {FARMER}, "scope": OWN_RECORDS},
    "offers.update_draft": {"roles": {FARMER}, "scope": OWN_RECORDS},
    "offers.publish": {"roles": {FARMER}, "scope": OWN_RECORDS},
    "offers.review": {"roles": {ADMIN, OPERATIONS_STAFF}, "scope": CONTEXTUAL},
    "offers.close": {"roles": {ADMIN, OPERATIONS_STAFF, FARMER}, "scope": CONTEXTUAL},
    "auctions.view": {
        "roles": {ADMIN, OPERATIONS_STAFF, AUDITOR, FARMER, TRADER},
        "scope": CONTEXTUAL,
    },
    "auctions.create": {"roles": {FARMER}, "scope": OWN_RECORDS},
    "auctions.place_bid": {"roles": {TRADER}, "scope": CONTEXTUAL},
    "auctions.close": {"roles": {ADMIN, OPERATIONS_STAFF, FARMER}, "scope": CONTEXTUAL},
    "orders.view": {
        "roles": {
            ADMIN,
            OPERATIONS_STAFF,
            DELIVERY_MANAGER,
            WAREHOUSE_MANAGER,
            WAREHOUSE_STAFF,
            QUALITY_MANAGER,
            AUDITOR,
            FARMER,
            TRADER,
            DRIVER,
            INSPECTOR,
        },
        "scope": CONTEXTUAL,
    },
    "orders.create": {"roles": {TRADER}, "scope": OWN_RECORDS},
    "orders.confirm": {"roles": {FARMER, TRADER, OPERATIONS_STAFF}, "scope": CONTEXTUAL},
    "orders.update_commercial_data": {"roles": {ADMIN}, "scope": GLOBAL},
    "orders.cancel": {"roles": {ADMIN, OPERATIONS_STAFF, FARMER, TRADER}, "scope": CONTEXTUAL},

    # --------------------------- Batches ----------------------------------
    "batches.view": {
        "roles": {
            ADMIN,
            OPERATIONS_STAFF,
            DELIVERY_MANAGER,
            WAREHOUSE_MANAGER,
            WAREHOUSE_STAFF,
            QUALITY_MANAGER,
            AUDITOR,
            FARMER,
            TRADER,
            DRIVER,
            INSPECTOR,
        },
        "scope": CONTEXTUAL,
    },
    "batches.create": {"roles": {OPERATIONS_STAFF, WAREHOUSE_MANAGER}, "scope": CONTEXTUAL},
    "batches.update_planning_data": {
        "roles": {ADMIN, OPERATIONS_STAFF},
        "scope": CONTEXTUAL,
    },

    # --------------------------- Delivery ---------------------------------
    "delivery.view": {
        "roles": {
            ADMIN,
            OPERATIONS_STAFF,
            DELIVERY_MANAGER,
            QUALITY_MANAGER,
            AUDITOR,
            FARMER,
            TRADER,
            DRIVER,
            INSPECTOR,
        },
        "scope": CONTEXTUAL,
    },
    "delivery.create_task": {"roles": {DELIVERY_MANAGER}, "scope": COMPANY},
    "delivery.assign_driver": {"roles": {DELIVERY_MANAGER}, "scope": COMPANY},
    "delivery.assign_vehicle": {"roles": {DELIVERY_MANAGER}, "scope": COMPANY},
    "delivery.update_status": {
        "roles": {DELIVERY_MANAGER, DRIVER},
        "scope": ASSIGNED_TASKS,
    },
    "delivery.record_incident": {
        "roles": {DELIVERY_MANAGER, DRIVER, INSPECTOR},
        "scope": CONTEXTUAL,
    },
    "delivery.reassign_task": {"roles": {DELIVERY_MANAGER}, "scope": COMPANY},

    # Requesting an inspector is not the same as assigning one.
    "handover.request_neutral_inspector": {
        "roles": {
            OPERATIONS_STAFF,
            DELIVERY_MANAGER,
            WAREHOUSE_MANAGER,
            QUALITY_MANAGER,
        },
        "scope": CONTEXTUAL,
    },
    # Final assignment is deliberately not granted to DELIVERY_MANAGER.
    "handover.assign_neutral_inspector": {
        "roles": {ADMIN},
        "scope": GLOBAL,
    },
    "handover.view": {
        "roles": {
            ADMIN,
            OPERATIONS_STAFF,
            DELIVERY_MANAGER,
            WAREHOUSE_MANAGER,
            WAREHOUSE_STAFF,
            QUALITY_MANAGER,
            AUDITOR,
            FARMER,
            TRADER,
            DRIVER,
            INSPECTOR,
        },
        "scope": CONTEXTUAL,
    },
    "handover.view_assigned": {"roles": {INSPECTOR}, "scope": ASSIGNED_HANDOVERS},
    "handover.accept_assignment": {"roles": {INSPECTOR}, "scope": ASSIGNED_HANDOVERS},
    "handover.reject_assignment": {"roles": {INSPECTOR}, "scope": ASSIGNED_HANDOVERS},
    "handover.start_inspection": {"roles": {INSPECTOR}, "scope": ASSIGNED_HANDOVERS},
    "handover.submit_report": {"roles": {INSPECTOR}, "scope": ASSIGNED_HANDOVERS},
    "handover.record_incident": {"roles": {INSPECTOR}, "scope": ASSIGNED_HANDOVERS},
    "handover.reassign_inspector": {"roles": {ADMIN}, "scope": GLOBAL},
    "handover.cancel_inspection": {
        "roles": {ADMIN, OPERATIONS_STAFF, QUALITY_MANAGER},
        "scope": CONTEXTUAL,
    },

    # --------------------------- Warehouses -------------------------------
    "storage.view": {
        "roles": {
            ADMIN,
            OPERATIONS_STAFF,
            WAREHOUSE_MANAGER,
            WAREHOUSE_STAFF,
            QUALITY_MANAGER,
            AUDITOR,
            DRIVER,
            INSPECTOR,
        },
        "scope": WAREHOUSE,
    },
    "storage.receive": {
        "roles": {WAREHOUSE_MANAGER, WAREHOUSE_STAFF},
        "scope": WAREHOUSE,
    },
    "storage.verify_receiving": {
    "roles": {
        "INSPECTOR",
    },
    "scope": "ASSIGNED_HANDOVERS",
    },

    "storage.internal_move": {
        "roles": {WAREHOUSE_MANAGER, WAREHOUSE_STAFF},
        "scope": WAREHOUSE,
    },
    # Physical release is a warehouse action, not an inspector action.
    "storage.release": {
        "roles": {WAREHOUSE_MANAGER, WAREHOUSE_STAFF},
        "scope": WAREHOUSE,
    },
    # Inspector verifies and documents; does not change stock.
    "storage.verify_release": {
        "roles": {INSPECTOR},
        "scope": ASSIGNED_HANDOVERS,
    },
    "storage.manage_zones": {"roles": {WAREHOUSE_MANAGER}, "scope": WAREHOUSE},
    "storage.manage_capacity": {"roles": {WAREHOUSE_MANAGER}, "scope": WAREHOUSE},

    # --------------------------- Quality and disputes ---------------------
    "disputes.view": {
        "roles": {ADMIN, OPERATIONS_STAFF, QUALITY_MANAGER, AUDITOR},
        "scope": CONTEXTUAL,
    },
    "disputes.view_own": {"roles": {FARMER, TRADER}, "scope": OWN_RECORDS},
    "disputes.open": {"roles": {FARMER, TRADER, OPERATIONS_STAFF}, "scope": CONTEXTUAL},
    "disputes.request_inspection": {
        "roles": {QUALITY_MANAGER, OPERATIONS_STAFF},
        "scope": CONTEXTUAL,
    },
    "disputes.review_evidence": {"roles": {QUALITY_MANAGER}, "scope": ASSIGNED_CASES},
    "quality.request_information": {"roles": {QUALITY_MANAGER}, "scope": ASSIGNED_CASES},
    "quality.decide": {"roles": {QUALITY_MANAGER}, "scope": ASSIGNED_CASES},
    "quality.close_case": {"roles": {QUALITY_MANAGER}, "scope": ASSIGNED_CASES},
    "quality.view_decisions": {
        "roles": {ADMIN, OPERATIONS_STAFF, QUALITY_MANAGER, AUDITOR, FARMER, TRADER},
        "scope": CONTEXTUAL,
    },

    # --------------------------- Audit and reports ------------------------
    "audit.view": {"roles": {ADMIN, AUDITOR}, "scope": GLOBAL},
    "audit.search": {"roles": {ADMIN, AUDITOR}, "scope": GLOBAL},
    "audit.export": {"roles": {ADMIN, AUDITOR}, "scope": GLOBAL},
    "reports.view": {
        "roles": {ADMIN, OPERATIONS_STAFF, QUALITY_MANAGER, DELIVERY_MANAGER, AUDITOR},
        "scope": CONTEXTUAL,
    },
    "reports.export": {"roles": {ADMIN, OPERATIONS_STAFF, AUDITOR}, "scope": CONTEXTUAL},
}


# ---------------------------------------------------------------------------
# Lightweight helpers for DRF permission classes and tests
# ---------------------------------------------------------------------------


def has_role_permission(role: str, permission: str) -> bool:
    """Return whether a role is listed for a permission."""
    rule = PERMISSIONS.get(permission)
    return bool(rule and role in rule["roles"])


def permission_scope(permission: str) -> str | None:
    """Return the configured scope, or None for an unknown permission."""
    rule = PERMISSIONS.get(permission)
    return None if rule is None else str(rule["scope"])


def validate_permission_catalog() -> list[str]:
    """Return catalog errors; an empty list means the catalog is structurally valid."""
    errors: list[str] = []
    for permission_name, rule in PERMISSIONS.items():
        if not permission_name or "." not in permission_name:
            errors.append(f"Invalid permission name: {permission_name!r}")
        roles = rule.get("roles")
        if not isinstance(roles, set):
            errors.append(f"{permission_name}: roles must be a set")
        elif not roles:
            errors.append(f"{permission_name}: roles cannot be empty")
        else:
            unknown_roles = set(roles) - ALL_ROLES
            if unknown_roles:
                errors.append(f"{permission_name}: unknown roles {sorted(unknown_roles)}")
        if not rule.get("scope"):
            errors.append(f"{permission_name}: scope is required")
    return errors


# These are business invariants, not role grants. Enforce them in services.
NEUTRAL_OBSERVER_RULES: Final[dict[str, object]] = {
    "assignment_target": "HANDOVER_POINT",
    "default_points": [HANDOVER_PICKUP, HANDOVER_RECEIVING],
    "different_inspector_per_point_by_default": True,
    "same_inspector_exception_requires_admin_reason": True,
    "inspector_must_have_role": INSPECTOR,
    "inspector_must_be_active": True,
    "inspector_must_be_available": True,
    "conflict_of_interest_is_forbidden": True,
    "inspector_cannot_be_driver_on_same_delivery": True,
    "inspector_cannot_be_farmer_or_trader_party": True,
    "inspector_can_record_facts_only": True,
    "inspector_cannot_decide_dispute": True,
    "quality_manager_decides_dispute": True,
    "warehouse_executes_release": True,
    "inspector_only_verifies_release": True,
}


if __name__ == "__main__":
    catalog_errors = validate_permission_catalog()
    if catalog_errors:
        raise SystemExit("\n".join(catalog_errors))
    print(f"Permission catalog is valid: {len(PERMISSIONS)} permissions")
