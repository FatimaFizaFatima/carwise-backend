from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.base_repo import BaseRepository
from app.models.notification import Notification


class NotificationRepository(BaseRepository[Notification]):

    def __init__(self, session: AsyncSession):
        super().__init__(session, Notification)

    def add_many(self, notifications: list[Notification]) -> None:
        self.session.add_all(notifications)

    async def get_for_user(
        self, user_id: int, unread_only: bool, limit: int, offset: int
    ) -> list[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read.is_(False))
        query = query.order_by(Notification.id.desc()).limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_unread(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
        )
        return result.scalar_one()

    async def get_owned(self, notification_id: int, user_id: int) -> Notification | None:
        result = await self.session.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def mark_all_read(self, user_id: int) -> int:
        result = await self.session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True, read_at=func.now())
            .execution_options(synchronize_session=False)
        )
        return result.rowcount