"""
قاموس الصلاحيات والأدوار والنطاقات لمنصة حصاد.

هذا الملف تعريف ثابت فقط؛ لا يطبق الصلاحيات على أي endpoint بعد.

القواعد المعتمدة:
- ADMIN يعيّن المراقب المحايد.
- DELIVERY_MANAGER يعيّن السائق والمركبة وينشئ مهام التوصيل.
- INSPECTOR يوثق الوقائع ولا يصدر قرار النزاع.
- QUALITY_MANAGER يصدر قرار النزاع.
"""

PERMISSIONS = {
    # Users and accounts
    "users.view": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "AUDITOR",
        },
        "scope": "GLOBAL",
    },
    "users.create_admin_account": {
        "roles": {
            "ADMIN",
        },
        "scope": "GLOBAL",
    },
    "users.activate": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
        },
        "scope": "GLOBAL",
    },
    "users.deactivate": {
        "roles": {
            "ADMIN",
        },
        "scope": "GLOBAL",
    },
    "users.assign_role": {
        "roles": {
            "ADMIN",
        },
        "scope": "GLOBAL",
    },

    # Offers, auctions, and bids
    "offers.view": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "AUDITOR",
            "FARMER",
            "TRADER",
        },
        "scope": "CONTEXTUAL",
    },
    "offers.create": {
        "roles": {
            "FARMER",
        },
        "scope": "OWNER",
    },
    "offers.review": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
        },
        "scope": "GLOBAL",
    },
    "offers.flag": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "AUDITOR",
        },
        "scope": "GLOBAL",
    },
    "auctions.view": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "AUDITOR",
            "FARMER",
            "TRADER",
        },
        "scope": "CONTEXTUAL",
    },
    "auctions.monitor": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "AUDITOR",
        },
        "scope": "GLOBAL",
    },
    "auctions.close": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
        },
        "scope": "GLOBAL",
    },
    "bids.view": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "AUDITOR",
            "TRADER",
        },
        "scope": "CONTEXTUAL",
    },

    # Orders and shipment batches
    "orders.view": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "AUDITOR",
            "FARMER",
            "TRADER",
            "INSPECTOR",
        },
        "scope": "CONTEXTUAL",
    },
    "orders.review": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
        },
        "scope": "GLOBAL",
    },
    "orders.update_operational_status": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
        },
        "scope": "GLOBAL",
    },
    "batches.view": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "AUDITOR",
            "FARMER",
            "TRADER",
            "DRIVER",
            "INSPECTOR",
            "WAREHOUSE_MANAGER",
            "WAREHOUSE_STAFF",
        },
        "scope": "CONTEXTUAL",
    },
    "batches.track": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "AUDITOR",
            "DELIVERY_MANAGER",
            "INSPECTOR",
            "WAREHOUSE_MANAGER",
            "WAREHOUSE_STAFF",
        },
        "scope": "CONTEXTUAL",
    },
    "batches.correct_with_new_record": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
        },
        "scope": "GLOBAL",
    },

    # Delivery and inspection assignment
    "delivery.view": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "DELIVERY_MANAGER",
            "DRIVER",
            "INSPECTOR",
            "AUDITOR",
        },
        "scope": "CONTEXTUAL",
    },
    "delivery.create_task": {
        "roles": {
            "DELIVERY_MANAGER",
        },
        "scope": "GLOBAL",
    },
    "delivery.assign_driver": {
        "roles": {
            "DELIVERY_MANAGER",
        },
        "scope": "COMPANY",
    },
    "delivery.assign_vehicle": {
        "roles": {
            "DELIVERY_MANAGER",
        },
        "scope": "COMPANY",
    },
    "delivery.assign_inspector": {
        "roles": {
            "ADMIN",
        },
        "scope": "GLOBAL",
    },
    "delivery.record_incident": {
        "roles": {
            "DRIVER",
            "INSPECTOR",
            "DELIVERY_MANAGER",
        },
        "scope": "ASSIGNED_TASKS",
    },

    # Warehouses and storage
    "warehouses.view": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "WAREHOUSE_MANAGER",
            "WAREHOUSE_STAFF",
            "AUDITOR",
            "TRADER",
            "FARMER",
        },
        "scope": "CONTEXTUAL",
    },
    "warehouses.manage_zones": {
        "roles": {
            "WAREHOUSE_MANAGER",
            "ADMIN",
        },
        "scope": "WAREHOUSE",
    },
    "storage.receive": {
        "roles": {
            "WAREHOUSE_MANAGER",
            "WAREHOUSE_STAFF",
        },
        "scope": "WAREHOUSE",
    },
    "storage.move_internal": {
        "roles": {
            "WAREHOUSE_MANAGER",
            "WAREHOUSE_STAFF",
        },
        "scope": "WAREHOUSE",
    },
    "storage.prepare_release": {
        "roles": {
            "WAREHOUSE_MANAGER",
            "WAREHOUSE_STAFF",
        },
        "scope": "WAREHOUSE",
    },
    "storage.release": {
        "roles": {
            "WAREHOUSE_MANAGER",
            "INSPECTOR",
        },
        "scope": "WAREHOUSE",
    },
    "storage.record_adjustment": {
        "roles": {
            "WAREHOUSE_MANAGER",
            "ADMIN",
        },
        "scope": "WAREHOUSE",
    },

    # Handovers and neutral inspection
    "handovers.view": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "QUALITY_MANAGER",
            "DELIVERY_MANAGER",
            "WAREHOUSE_MANAGER",
            "AUDITOR",
            "FARMER",
            "TRADER",
            "DRIVER",
            "INSPECTOR",
        },
        "scope": "CONTEXTUAL",
    },
    "handovers.view_evidence": {
        "roles": {
            "ADMIN",
            "QUALITY_MANAGER",
            "AUDITOR",
        },
        "scope": "CONTEXTUAL",
    },
    "handovers.create": {
        "roles": {
            "INSPECTOR",
        },
        "scope": "ASSIGNED_TASKS",
    },
    "handovers.create_correction": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
        },
        "scope": "CONTEXTUAL",
    },

    # Disputes and quality decisions
    "disputes.view": {
        "roles": {
            "ADMIN",
            "OPERATIONS_STAFF",
            "QUALITY_MANAGER",
            "AUDITOR",
        },
        "scope": "CONTEXTUAL",
    },
    "disputes.review_evidence": {
        "roles": {
            "QUALITY_MANAGER",
        },
        "scope": "ASSIGNED_CASES",
    },
    "quality.decide": {
        "roles": {
            "QUALITY_MANAGER",
        },
        "scope": "ASSIGNED_CASES",
    },
    "quality.close_case": {
        "roles": {
            "QUALITY_MANAGER",
        },
        "scope": "ASSIGNED_CASES",
    },

    # Audit
    "audit.view": {
        "roles": {
            "ADMIN",
            "AUDITOR",
        },
        "scope": "GLOBAL",
    },
    "audit.search": {
        "roles": {
            "ADMIN",
            "AUDITOR",
        },
        "scope": "GLOBAL",
    },
    "audit.export": {
        "roles": {
            "ADMIN",
            "AUDITOR",
        },
        "scope": "GLOBAL",
    },
}
