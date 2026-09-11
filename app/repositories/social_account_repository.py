from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base_repo import BaseRepository
from app.models.social_account import SocialAccount


class SocialAccountRepository(BaseRepository[SocialAccount]):

    def __init__(self, session : AsyncSession):
        super().__init__(session, SocialAccount)


    async def get_by_provider(self, provider : str, provider_user_id : str) -> SocialAccount | None:
        result = await self.session.execute(select(SocialAccount).where(SocialAccount.provider == provider, SocialAccount.provider_user_id == provider_user_id))
        return result.scalar_one_or_none()    