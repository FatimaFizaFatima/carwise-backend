from datetime import date, datetime
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey, Index, text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class Car(Base):
    __tablename__ = "cars"
    __table_args__ = (
        Index(
            "ix_cars_registration_no_active",
            "registration_no",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "ix_cars_engine_number_active",
            "engine_number",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    registration_no: Mapped[str] = mapped_column(String(20), nullable=False)   # unique=True removed
    owner_name: Mapped[str] = mapped_column(String(100), nullable=False)
    make: Mapped[str] = mapped_column(String(50), nullable=False)
    vehicle_model: Mapped[str] = mapped_column(String(50), nullable=False)
    model_year: Mapped[int] = mapped_column(Integer, nullable=False)
    registration_date: Mapped[date] = mapped_column(Date, nullable=False)

    provision: Mapped[str | None] = mapped_column(String(50), nullable=True)
    body_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    class_of_vehicle: Mapped[str | None] = mapped_column(String(20), nullable=True)
    engine_number: Mapped[str | None] = mapped_column(String(50), nullable=True)   # unique=True removed
    engine_capacity_cc: Mapped[int | None] = mapped_column(Integer, nullable=True)
    seating_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )