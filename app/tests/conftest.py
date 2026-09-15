import uuid

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.db.database import engine
from app.unit_of_work.unit_of_work import UnitOfWork
from app.models.user_models import User
from app.core.roles import Role, AccountStatus
from app.core.securtiy import hash_password, create_access_token


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine_after_each_test():
    """
    pytest-asyncio gives each test its own event loop by default, but the
    app's async engine/connection pool is created once at import time and
    holds onto real asyncpg connections tied to whichever loop created them.
    Reusing them from a different test's loop causes
    'cannot perform operation: another operation is in progress' errors.
    Disposing the pool after every test forces fresh connections to be
    opened under the next test's own event loop.
    """
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def client():
    """An httpx client that talks directly to the FastAPI app (no real network/port)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_cleanup():
    """
    Tests append ids of rows they create here. After the test finishes
    (pass or fail), those rows are hard-deleted from the DB so the test
    suite doesn't leave junk behind or collide with itself on reruns.
    Cars are deleted before users to avoid FK issues.
    """
    created_car_ids: list[int] = []
    created_user_ids: list[int] = []

    yield created_car_ids, created_user_ids

    async with UnitOfWork() as uow:
        for car_id in created_car_ids:
            car = await uow.cars.get_by_id(car_id)
            if car is not None:
                await uow.cars.delete(car)

        for user_id in created_user_ids:
            user = await uow.users.get_by_id(user_id)
            if user is not None:
                await uow.users.delete(user)

        await uow.commit()


@pytest_asyncio.fixture
async def user_factory(db_cleanup):
    """
    Returns an async factory: await user_factory(role=..., status=...)
    -> (user, auth_headers). Created users are auto-cleaned via db_cleanup.
    """
    created_car_ids, created_user_ids = db_cleanup

    async def _create(role: str = Role.CUSTOMER, status: str = AccountStatus.ACTIVE) -> tuple[User, dict]:
        unique = uuid.uuid4().hex[:10]
        async with UnitOfWork() as uow:
            user = User(
                full_name="Test User",
                email=f"test_{unique}@example.com",
                phone=f"030{unique[:8]}",
                password_hash=hash_password("Test@1234"),
                role=role,
                status=status,
                email_verified=True,
            )
            uow.users.add(user)
            await uow.commit()
            await uow.session.refresh(user)

        created_user_ids.append(user.id)
        token = create_access_token({"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {token}"}
        return user, headers

    return _create


def car_payload(**overrides) -> dict:
    """A valid CarCreateRequest body with unique registration/engine numbers by default."""
    unique = uuid.uuid4().hex[:8].upper()
    payload = {
        "registration_no": f"REG-{unique}",
        "owner_name": "Test Owner",
        "make": "Toyota",
        "vehicle_model": "Corolla",
        "model_year": 2022,
        "registration_date": "2022-01-15",
        "engine_number": f"ENG-{unique}",
    }
    payload.update(overrides)
    return payload