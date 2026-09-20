# app/models/workshop.py
from datetime import datetime, time
from sqlalchemy import String, DateTime, Float, Time, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.core.roles import WorkshopStatus


class Workshop(Base):
    __tablename__ = "workshops"

    id: Mapped[int] = mapped_column(primary_key=True)
    workshop_name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=WorkshopStatus.PENDING, server_default=WorkshopStatus.PENDING
    )
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    avg_rating: Mapped[float] = mapped_column(Float, nullable=False, default=0.0, server_default="0")
    opens_at: Mapped[time | None] = mapped_column(Time, nullable=True)
    closes_at: Mapped[time | None] = mapped_column(Time, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )