from app.repositories.base_repo import BaseRepository
from app.models.service_history import ServiceHistory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.booking import Booking

class ServiceHistoryRepository(BaseRepository[ServiceHistory]):

    def __init__(self, session : AsyncSession):
        super().__init__(session, ServiceHistory)


    async def get_service_history_by_user_cars(self, car_ids : list[int], limit : int, offset : int):
        result = await self.session.execute(select(ServiceHistory).where(ServiceHistory.car_id.in_(car_ids), ServiceHistory.booking_id.is_not(None)).order_by(ServiceHistory.service_date.desc()).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def get_expense_history_by_user_cars(self, car_ids : list[int], limit : int, offset : int):
        result = await self.session.execute(select(ServiceHistory).where(ServiceHistory.car_id.in_(car_ids), ServiceHistory.booking_id.is_(None)).order_by(ServiceHistory.service_date.desc()).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def get_by_car(self, car_id : int, limit : int, offset : int):
        result = await self.session.execute(select(ServiceHistory).where(ServiceHistory.car_id == car_id).order_by(ServiceHistory.service_date.desc()).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def get_by_workshop(self, workshop_id : int, limit : int, offset : int):
        result = await self.session.execute(select(ServiceHistory).join(Booking, Booking.id == ServiceHistory.booking_id).where(Booking.workshop_id == workshop_id).order_by(ServiceHistory.service_date.desc()).limit(limit).offset(offset))
        return list(result.scalars().all())

    async def get_all(self, limit : int, offset : int):
        result = await self.session.execute(select(ServiceHistory).order_by(ServiceHistory.service_date.desc()).limit(limit).offset(offset))
        return list(result.scalars().all())