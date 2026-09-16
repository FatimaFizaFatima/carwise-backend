from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workshop import Workshop
from app.repositories.base_repo import BaseRepository


class WorkshopRepository(BaseRepository[Workshop]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Workshop)