from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.booking import Booking
from app.repositories.base_repo import BaseRepository
from app.core.roles import BookingStatus


class BookingRepository(BaseRepository[Booking]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Booking)

    async def get_by_user(self, user_id: int) -> list[Booking]:
        result = await self.session.execute(select(Booking).where(Booking.user_id == user_id))
        return list(result.scalars().all())

    async def get_all(self) -> list[Booking]:
        result = await self.session.execute(select(Booking))
        return list(result.scalars().all())

    async def get_by_workshop(self, workshop_id: int) -> list[Booking]:
        result = await self.session.execute(select(Booking).where(Booking.workshop_id == workshop_id))
        return list(result.scalars().all())

   