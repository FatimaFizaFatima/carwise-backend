from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repo import BaseRepository
from app.models.otp_code import OtpCode

class OTPCodeRepository(BaseRepository[OtpCode]):

    def __init__(self, session : AsyncSession):
        super().__init__(session, OtpCode)

    async def get_latest_active(self, user_id : int, purpose : str)->OtpCode | None:
        result = await self.session.execute(select(OtpCode).where(
            OtpCode.user_id == user_id,
            OtpCode.purpose == purpose,
            OtpCode.consumed_at.is_(None),
        ).order_by(OtpCode.created_at.desc()))

        return result.scalars().first()     