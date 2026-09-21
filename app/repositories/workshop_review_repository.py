from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workshop_review import WorkshopReview
from app.repositories.base_repo import BaseRepository


class WorkshopReviewRepository(BaseRepository[WorkshopReview]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkshopReview)

    async def get_by_workshop(self, workshop_id: int) -> list[WorkshopReview]:
        result = await self.session.execute(
            select(WorkshopReview).where(WorkshopReview.workshop_id == workshop_id)
        )
        return list(result.scalars().all())

    async def exists_for_booking(self, booking_id: int) -> bool:
        result = await self.session.execute(
            select(WorkshopReview.id).where(WorkshopReview.booking_id == booking_id)
        )
        return result.scalar_one_or_none() is not None

    async def get_average_rating(self, workshop_id: int) -> float:
        from sqlalchemy import func
        result = await self.session.execute(
            select(func.avg(WorkshopReview.rating)).where(WorkshopReview.workshop_id == workshop_id)
        )
        avg = result.scalar_one_or_none()
        return round(float(avg), 2) if avg is not None else 0.0