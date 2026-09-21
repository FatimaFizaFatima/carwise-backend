from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workshop_service import WorkshopService
from app.repositories.base_repo import BaseRepository


class WorkshopServiceRepository(BaseRepository[WorkshopService]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, WorkshopService)

    async def get_by_workshop(self, workshop_id: int) -> list[WorkshopService]:
        result = await self.session.execute(
            select(WorkshopService).where(WorkshopService.workshop_id == workshop_id)
        )
        return list(result.scalars().all())

    async def exists_for_workshop(self, workshop_id: int, category_id: int) -> bool:
        result = await self.session.execute(
            select(WorkshopService.id).where(
                WorkshopService.workshop_id == workshop_id,
                WorkshopService.category_id == category_id,
            )
        )
        return result.scalar_one_or_none() is not None