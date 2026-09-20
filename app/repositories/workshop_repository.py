from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workshop import Workshop
from app.models.workshop_service import WorkshopService
from app.repositories.base_repo import BaseRepository
from sqlalchemy import select, func
from app.core.roles import WorkshopStatus

class WorkshopRepository(BaseRepository[Workshop]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Workshop)


    async def search_nearby(self, lat: float, lng: float, radius_km: float, limit: int = 20, offset: int = 0) -> list[tuple]:
   
        distance_expr = (
            6371 * func.acos(
            func.cos(func.radians(lat))
            * func.cos(func.radians(self.model.latitude))
            * func.cos(func.radians(self.model.longitude) - func.radians(lng))
            + func.sin(func.radians(lat))
            * func.sin(func.radians(self.model.latitude))
            )
        ).label("distance_km")

        stmt = (
            select(self.model, distance_expr)
            .where(self.model.status == WorkshopStatus.APPROVED)
            .where(distance_expr <= radius_km)
            .order_by(distance_expr)
            .limit(limit)
            .offset(offset)
            )
        result = await self.session.execute(stmt)
        return result.all()
    async def search(self, category_id: int | None, min_price: float | None, max_price: float | None, sort_by: str, limit: int, offset: int,) -> list[Workshop]:

        stmt = select(Workshop).where(Workshop.status == WorkshopStatus.APPROVED)

        if category_id is not None or min_price is not None or max_price is not None:
            stmt = stmt.join(WorkshopService, WorkshopService.workshop_id == Workshop.id)
            if category_id is not None:
                stmt = stmt.where(WorkshopService.category_id == category_id)
            if min_price is not None:
                stmt = stmt.where(WorkshopService.price >= min_price)
            if max_price is not None:
                stmt = stmt.where(WorkshopService.price <= max_price)
        stmt = stmt.distinct()

        if sort_by == "rating":
            stmt = stmt.order_by(Workshop.avg_rating.desc())
        else:
            stmt = stmt.order_by(Workshop.workshop_name.asc())

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())    

    async def count_search(self, category_id: int | None, min_price: float | None, max_price: float | None) -> int:
        stmt = select(func.count(func.distinct(Workshop.id))).where(Workshop.status == WorkshopStatus.APPROVED)
        if category_id is not None or min_price is not None or max_price is not None:
            stmt = stmt.join(WorkshopService, WorkshopService.workshop_id == Workshop.id)
            if category_id is not None:
                stmt = stmt.where(WorkshopService.category_id == category_id)
            if min_price is not None:
                stmt = stmt.where(WorkshopService.price >= min_price)
            if max_price is not None:
                stmt = stmt.where(WorkshopService.price <= max_price)

        result = await self.session.execute(stmt)
        return result.scalar_one()    