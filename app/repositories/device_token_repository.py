from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.repositories.base_repo import BaseRepository
from app.models.device_token import DeviceToken


class DeviceTokenRepository(BaseRepository[DeviceToken]):

    def __init__(self, session: AsyncSession):
        super().__init__(session, DeviceToken)

    async def get_by_token(self, token: str) -> DeviceToken | None:
        result = await self.session.execute(select(DeviceToken).where(DeviceToken.token == token))
        return result.scalar_one_or_none()

    async def get_active_by_user(self, user_id: int) -> list[DeviceToken]:
        result = await self.session.execute(
            select(DeviceToken).where(DeviceToken.user_id == user_id, DeviceToken.is_active == True)  
        )
        return list(result.scalars().all())

    async def get_all_active(self) -> list[DeviceToken]:
        result = await self.session.execute(select(DeviceToken).where(DeviceToken.is_active == True))  
        return list(result.scalars().all())

    async def deactivate(self, token: str, user_id: int) -> DeviceToken | None:
        device_token = await self.get_by_token(token)
        if device_token is None or device_token.user_id != user_id:
            return None
        device_token.is_active = False
        return device_token