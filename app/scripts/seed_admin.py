import asyncio
from app.db.database import SessionLocal
from app.models.user_models import User
from app.core.securtiy import hash_password
from app.core.config import settings
from app.core.roles import Role, AccountStatus
from app.models.workshop import Workshop


async def seed_admin():
    async with SessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        existing = result.scalar_one_or_none()

        if existing is not None:
            print(f"Admin already exists: {existing.email}")
            return

        admin = User(
            full_name="CarWise Admin",
            email=settings.ADMIN_EMAIL,
            phone=None,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role=Role.ADMIN,
            status=AccountStatus.ACTIVE,
            email_verified=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Admin created: {admin.email}")


if __name__ == "__main__":
    asyncio.run(seed_admin())