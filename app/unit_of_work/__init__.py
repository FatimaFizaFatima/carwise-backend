from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.repositories.otp_code_repository import OTPCodeRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.social_account_repository import SocialAccountRepository

class UnitOfWork():
    def __init__(self):
        self.session : AsyncSession = SessionLocal()
        self.users = UserRepository(self.session)
        self.otp_codes = OTPCodeRepository(self.session)
        self.refresh_tokens = RefreshTokenRepository(self.session)
        self.social_accounts = SocialAccountRepository(self.session)


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