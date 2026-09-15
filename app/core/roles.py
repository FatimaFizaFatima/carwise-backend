class Role:
    """User roles supported by the system, per product decision:
    Admin, Workshop Staff, Customer (no sub-roles within Workshop Staff)."""

    ADMIN = "admin"
    WORKSHOP_STAFF = "workshop_staff"
    CUSTOMER = "customer"

    ALL = (ADMIN, WORKSHOP_STAFF, CUSTOMER)


class AccountStatus:
    """Lifecycle status of a user account, independent of role."""

    ACTIVE = "active"
    PENDING_APPROVAL = "pending_approval"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class WorkshopStatus:
    """Lifecycle status of a workshop record."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUSPENDED = "suspended"
