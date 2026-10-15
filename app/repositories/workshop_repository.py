from math import cos, radians

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import WorkshopStatus
from app.models.workshop import Workshop
from app.models.workshop_service import WorkshopService
from app.repositories.base_repo import BaseRepository


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _name_matches(q: str):
    return Workshop.workshop_name.ilike(f"%{_escape_like(q)}%", escape="\\")


class WorkshopRepository(BaseRepository[Workshop]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Workshop)


    async def search_nearby(
        self, lat: float, lng: float, radius_km: float, limit: int = 20, offset: int = 0
    ) -> list[tuple]:
       
        cos_angle = (
            func.cos(func.radians(lat))
            * func.cos(func.radians(Workshop.latitude))
            * func.cos(func.radians(Workshop.longitude) - func.radians(lng))
            + func.sin(func.radians(lat)) * func.sin(func.radians(Workshop.latitude))
        )
        distance_expr = (
            6371 * func.acos(func.least(1.0, func.greatest(-1.0, cos_angle)))
        ).label("distance_km")

        
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / (111.0 * max(cos(radians(lat)), 1e-6))
        conditions = [
            Workshop.status == WorkshopStatus.APPROVED,
            Workshop.latitude.is_not(None),
            Workshop.longitude.is_not(None),
            Workshop.latitude.between(lat - lat_delta, lat + lat_delta),
        ]
        if lng - lng_delta >= -180 and lng + lng_delta <= 180:
            conditions.append(Workshop.longitude.between(lng - lng_delta, lng + lng_delta))

        stmt = (
            select(Workshop, distance_expr)
            .where(*conditions)
            .where(distance_expr <= radius_km)
            .order_by(distance_expr, Workshop.id.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(stmt)
        return result.all()

    @staticmethod
    def _apply_search_filters(stmt, category_id, min_price, max_price, min_rating, q):
        if category_id is not None or min_price is not None or max_price is not None:
            stmt = stmt.join(WorkshopService, WorkshopService.workshop_id == Workshop.id)
            if category_id is not None:
                stmt = stmt.where(WorkshopService.category_id == category_id)
            if min_price is not None:
                stmt = stmt.where(WorkshopService.price >= min_price)
            if max_price is not None:
                stmt = stmt.where(WorkshopService.price <= max_price)
        if min_rating is not None:
            stmt = stmt.where(Workshop.avg_rating >= min_rating)
        if q:
            stmt = stmt.where(_name_matches(q))
        return stmt

    async def search(
        self, q: str | None, category_id: int | None, min_price: float | None, max_price: float | None,
        min_rating: float | None, sort_by: str, limit: int, offset: int,
    ) -> list[Workshop]:
        stmt = select(Workshop).where(Workshop.status == WorkshopStatus.APPROVED)
        stmt = self._apply_search_filters(stmt, category_id, min_price, max_price, min_rating, q)
        stmt = stmt.distinct()

        if sort_by == "rating":
            stmt = stmt.order_by(Workshop.avg_rating.desc(), Workshop.id.asc())
        else:
            stmt = stmt.order_by(Workshop.workshop_name.asc(), Workshop.id.asc())

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_search(
        self, q: str | None, category_id: int | None, min_price: float | None, max_price: float | None,
        min_rating: float | None,
    ) -> int:
        stmt = select(func.count(func.distinct(Workshop.id))).where(Workshop.status == WorkshopStatus.APPROVED)
        stmt = self._apply_search_filters(stmt, category_id, min_price, max_price, min_rating, q)
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    async def list_admin(self, status: str | None, q: str | None, limit: int, offset: int) -> list[Workshop]:
        stmt = select(Workshop)
        if status:
            stmt = stmt.where(Workshop.status == status)
        if q:
            stmt = stmt.where(_name_matches(q))
        stmt = stmt.order_by(Workshop.id.desc()).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_admin(self, status: str | None, q: str | None) -> int:
        stmt = select(func.count(Workshop.id))
        if status:
            stmt = stmt.where(Workshop.status == status)
        if q:
            stmt = stmt.where(_name_matches(q))
        result = await self.session.execute(stmt)
        return result.scalar_one()
