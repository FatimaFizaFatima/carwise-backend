from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, ForeignKey, func, DateTime, Date
from datetime import datetime, date

class ServiceHistory(Base):

    __tablename__ = "service_history"

    id : Mapped[int] = mapped_column(primary_key=True)
    car_id : Mapped[int] = mapped_column(ForeignKey("cars.id"), nullable=False)
    booking_id: Mapped[int | None] = mapped_column(ForeignKey("bookings.id"), nullable=True, unique=True)
    title : Mapped[str] = mapped_column(String, nullable=False)
    cost : Mapped[float] = mapped_column(Float, nullable=False)
    service_details : Mapped[str | None] = mapped_column(String, nullable=True)
    workshop_name : Mapped[str] = mapped_column(String, nullable=True)
    attachment_url: Mapped[str | None] = mapped_column(String, nullable=True)
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now()) 
