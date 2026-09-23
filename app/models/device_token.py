from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Boolean, String, ForeignKey, DateTime, func
from datetime import datetime

class DeviceToken(Base):

    __tablename__ = "device_tokens"
    id : Mapped[int] = mapped_column(primary_key=True)
    user_id : Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    token : Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    device_type: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )