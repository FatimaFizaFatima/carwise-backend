from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repo import BaseRepository
from app.models.conversation import Conversation


class ConversationRepository(BaseRepository[Conversation]):

    def __init__(self, session: AsyncSession):
        super().__init__(session, Conversation)

    async def get_by_booking_id(self, booking_id: int) -> Conversation | None:
        result = await self.session.execute(
            select(Conversation).where(Conversation.booking_id == booking_id)
        )
        return result.scalar_one_or_none()

    async def get_for_customer(self, customer_id: int) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.customer_id == customer_id)
            .order_by(Conversation.last_message_at.desc().nulls_last(), Conversation.id.desc())
        )
        return list(result.scalars().all())

    async def get_for_workshop(self, workshop_id: int) -> list[Conversation]:
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.workshop_id == workshop_id)
            .order_by(Conversation.last_message_at.desc().nulls_last(), Conversation.id.desc())
        )
        return list(result.scalars().all())