from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.repositories.otp_code_repository import OTPCodeRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.social_account_repository import SocialAccountRepository
from app.repositories.car_repository import CarRepository
from app.repositories.workshop_repository import WorkshopRepository
from app.repositories.service_category_repository import ServiceCategoryRepository
from app.repositories.workshop_service_repository import WorkshopServiceRepository
from app.repositories.booking_repository import BookingRepository
from app.repositories.booking_item_repository import BookingItemRepository
from app.repositories.workshop_review_repository import WorkshopReviewRepository
from app.repositories.service_history_repository import ServiceHistoryRepository
from app.repositories.device_token_repository import DeviceTokenRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.notification_repository import NotificationRepository
class UnitOfWork():
    def __init__(self):
        self.session : AsyncSession = SessionLocal()
        self.users = UserRepository(self.session)
        self.otp_codes = OTPCodeRepository(self.session)
        self.refresh_tokens = RefreshTokenRepository(self.session)
        self.social_accounts = SocialAccountRepository(self.session)
        self.cars = CarRepository(self.session)
        self.workshops = WorkshopRepository(self.session)
        self.service_categories = ServiceCategoryRepository(self.session)
        self.workshop_services = WorkshopServiceRepository(self.session)
        self.bookings = BookingRepository(self.session)
        self.booking_items = BookingItemRepository(self.session)
        self.workshop_reviews = WorkshopReviewRepository(self.session)
        self.service_history = ServiceHistoryRepository(self.session)
        self.device_tokens = DeviceTokenRepository(self.session)
        self.conversations = ConversationRepository(self.session)
        self.messages = MessageRepository(self.session)
        self.notifications = NotificationRepository(self.session)


    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type is not None:
            await self.rollback() 

        return await self.session.close()

    async def commit(self):
        return await self.session.commit()

    async def rollback(self):
        return await self.session.rollback()        