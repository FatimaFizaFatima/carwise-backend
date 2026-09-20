from datetime import datetime, date, time
from sqlalchemy import String, Date, Time, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.core.roles import BookingStatus


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_reference: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    car_id: Mapped[int] = mapped_column(ForeignKey("cars.id"), nullable=False)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id"), nullable=False)

    service_type: Mapped[str] = mapped_column(String(20), nullable=False)  
    pickup_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    delivery_address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)

    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    scheduled_time: Mapped[time] = mapped_column(Time, nullable=False)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default=BookingStatus.PENDING,
                                         server_default=BookingStatus.PENDING)
    total_price: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BookingItem(Base):
    __tablename__ = "booking_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    booking_id: Mapped[int] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    workshop_service_id: Mapped[int] = mapped_column(ForeignKey("workshop_services.id"), nullable=False)
    price_snapshot: Mapped[float] = mapped_column(Float, nullable=False)