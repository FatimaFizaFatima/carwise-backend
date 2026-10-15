from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Float, DateTime, Index, func, ForeignKey
from datetime import datetime


class WorkshopService(Base):

    __tablename__ = "workshop_services"
    __table_args__ = (
        Index("uq_workshop_services_workshop_category", "workshop_id", "category_id", unique=True),
        Index("ix_workshop_services_category_id", "category_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("service_categories.id"), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
