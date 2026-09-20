from app.repositories.base_repo import BaseRepository
from app.models.service_category import ServiceCategoryModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

class ServiceCategoryRepository(BaseRepository[ServiceCategoryModel]):

    def __init__(self, session : AsyncSession):
        super().__init__(session, ServiceCategoryModel)

    async def get_all(self) -> list[ServiceCategoryModel]:
        result = await self.session.execute(select(ServiceCategoryModel))
        return list(result.scalars().all())

    async def get_by_name(self, name : str) -> ServiceCategoryModel | None:
        result = await self.session.execute(select(ServiceCategoryModel).where(ServiceCategoryModel.name == name))
        return result.scalar_one_or_none()

        