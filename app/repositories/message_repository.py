from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repo import BaseRepository
from app.models.message import Message
from app.core.roles import MessageStatus


class MessageRepository(BaseRepository[Message]):

    def __init__(self, session: AsyncSession):
        super().__init__(session, Message)

    async def get_history(
        self, conversation_id: int, before_id: int | None = None, limit: int = 30
    ) -> list[Message]:
        query = select(Message).where(Message.conversation_id == conversation_id)
        if before_id is not None:
            query = query.where(Message.id < before_id)
        query = query.order_by(Message.id.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_after(
        self, conversation_id: int, after_id: int, limit: int = 100
    ) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id, Message.id > after_id)
            .order_by(Message.id.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_last(self, conversation_id: int) -> Message | None:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_unread(
        self, conversation_id: int, customer_id: int, for_customer: bool
    ) -> int:
        query = select(func.count()).select_from(Message).where(
            Message.conversation_id == conversation_id,
            Message.status != MessageStatus.READ,
        )
        if for_customer:
            query = query.where(Message.sender_id != customer_id)
        else:
            query = query.where(Message.sender_id == customer_id)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def mark_read(
        self, conversation_id: int, customer_id: int, for_customer: bool, up_to_id: int
    ) -> list[int]:
        stmt = update(Message).where(
            Message.conversation_id == conversation_id,
            Message.id <= up_to_id,
            Message.status != MessageStatus.READ,
        )
        if for_customer:
            stmt = stmt.where(Message.sender_id != customer_id)
        else:
            stmt = stmt.where(Message.sender_id == customer_id)

        stmt = (
            stmt.values(
                status=MessageStatus.READ,
                read_at=func.now(),
                delivered_at=func.coalesce(Message.delivered_at, func.now()),
            )
            .returning(Message.id)
            .execution_options(synchronize_session=False)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())