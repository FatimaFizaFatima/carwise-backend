from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends
from app.unit_of_work.unit_of_work import UnitOfWork
from app.core.securtiy import decode_token
from app.core.exceptions import AppException
from app.models.user_models import User
from app.core.roles import AccountStatus

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> User:
    if credentials is None:
        raise AppException("Not authenticated", status_code=401)

    token = credentials.credentials
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise AppException("Invalid token type", status_code=401)

    user_id = payload.get("sub")
    if not user_id:
        raise AppException("Invalid token payload", status_code=401)

    async with UnitOfWork() as uow:
        user = await uow.users.get_by_id(int(user_id))
        if user is None:
            raise AppException("User not found", status_code=401)
        if user.status != AccountStatus.ACTIVE:
            raise AppException("Account is not active", status_code=403)
        return user
