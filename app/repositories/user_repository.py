from sqlalchemy.ext.asyncio import AsyncSession
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

    async def exist_by_user_email_or_phone(self, email : str, phone : str)->bool:
        result = await self.session.execute(select(User).where(or_(User.email == email, User.phone == phone)))
        return result.scalar_one_or_none() is not None