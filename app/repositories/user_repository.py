from sqlalchemy.ext.asyncio import AsyncSession
from app.core.roles import AccountStatus, Role
from app.repositories.base_repo import BaseRepository
from app.models.user_models import User
from sqlalchemy import select, or_


class UserRepository(BaseRepository[User]):

    def __init__(self, session : AsyncSession):
        super().__init__(session, User)


    async def get_user_by_email(self, email : str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_phone(self, phone : str)-> User | None:
        result = await self.session.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_user_by_identifier(self, identifier : str) -> User | None:
        result = await self.session.execute(select(User).where(or_(User.email == identifier, User.phone == identifier)))
        return result.scalar_one_or_none()        

    async def exists_by_email_or_phone(self, email : str, phone : str)->bool:
        result = await self.session.execute(select(User).where(or_(User.email == email, User.phone == phone)))
        return result.scalar_one_or_none() is not None

    async def get_active_staff_ids_by_workshop(self, workshop_id: int) -> list[int]:
        result = await self.session.execute(
            select(User.id).where(
                User.role == Role.WORKSHOP_STAFF,
                User.workshop_id == workshop_id,
                User.status == AccountStatus.ACTIVE,
            )
        )
        return list(result.scalars().all())