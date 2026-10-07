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


class BookingStatus:
    PENDING = "pending"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    ACTIVE = (PENDING, CONFIRMED, IN_PROGRESS)


class MessageStatus:
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


class NotificationType:
    """Notification event types sent via OneSignal. Used in the push payload's
    data.type field so the mobile app knows how to deep-link on tap."""

    BOOKING_CREATED = "booking_created"
    BOOKING_CONFIRMED = "booking_confirmed"
    BOOKING_STATUS_UPDATED = "booking_status_updated"
    BOOKING_CANCELLED = "booking_cancelled"
    BOOKING_RESCHEDULED = "booking_rescheduled"
    SERVICE_REMINDER = "service_reminder"
    NEW_CHAT_MESSAGE = "new_chat_message"
    PROMOTIONAL_OFFER = "promotional_offer"
    SYSTEM_MAINTENANCE = "system_maintenance"
    GENERAL = "general"