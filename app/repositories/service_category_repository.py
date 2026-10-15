from app.repositories.base_repo import BaseRepository
from app.models.service_category import ServiceCategoryModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


class ServiceCategoryRepository(BaseRepository[ServiceCategoryModel]):

    def __init__(self, session: AsyncSession):
        super().__init__(session, ServiceCategoryModel)

    async def get_all(self) -> list[ServiceCategoryModel]:
        result = await self.session.execute(
            select(ServiceCategoryModel).order_by(ServiceCategoryModel.id.asc())
        )
        return list(result.scalars().all())

    async def get_by_name(self, name: str, exclude_id: int | None = None) -> ServiceCategoryModel | None:
        """Case-insensitive lookup, so 'Oil Change' and 'oil change' count as duplicates."""
        stmt = select(ServiceCategoryModel).where(func.lower(ServiceCategoryModel.name) == name.lower())
        if exclude_id is not None:
            stmt = stmt.where(ServiceCategoryModel.id != exclude_id)
        result = await self.session.execute(stmt.limit(1))
        return result.scalar_one_or_none()
