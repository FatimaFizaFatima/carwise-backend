from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.booking import BookingItem
from app.repositories.base_repo import BaseRepository


class BookingItemRepository(BaseRepository[BookingItem]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, BookingItem)

    async def get_by_booking(self, booking_id: int) -> list[BookingItem]:
        result = await self.session.execute(
            select(BookingItem).where(BookingItem.booking_id == booking_id)
        )
        return list(result.scalars().all())