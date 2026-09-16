from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cars import Car
from app.repositories.base_repo import BaseRepository


class CarRepository(BaseRepository[Car]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Car)

    async def get_active_by_id(self, car_id: int) -> Car | None:
        result = await self.session.execute(
            select(Car).where(Car.id == car_id, Car.deleted_at.is_(None))
        )
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int) -> list[Car]:
        result = await self.session.execute(
            select(Car).where(Car.user_id == user_id, Car.deleted_at.is_(None))
        )
        return list(result.scalars().all())

    async def exists_by_registration_or_engine(
        self, registration_no: str, engine_number: str | None
    ) -> bool:
        conditions = [Car.registration_no == registration_no]
        if engine_number is not None:
            conditions.append(Car.engine_number == engine_number)

        result = await self.session.execute(
        select(Car.id).where(or_(*conditions), Car.deleted_at.is_(None))   
    )
        return result.scalar_one_or_none() is not None