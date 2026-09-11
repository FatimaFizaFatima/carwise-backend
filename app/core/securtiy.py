from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
from jwt import InvalidTokenError, ExpiredSignatureError
from app.core.config import settings
from app.core.exceptions import AppException


pwd_context = CryptContext(
    schemes=['bcrypt'],
    deprecated = "auto"
)

def hash_password(password : str)->str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hash_password: str)->bool:
    return pwd_context.verify(plain_password, hash_password)

def create_access_token(data : dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

def create_refresh_token(data : dict)->str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm= settings.ALGORITHM
    )

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except ExpiredSignatureError:
        raise AppException("Token has expired", status_code=401)
    except InvalidTokenError:
        raise AppException("Invalid token", status_code=401)

def create_reset_token(user_id: int) -> str:
    to_encode = {"sub": str(user_id), "purpose": "password_reset"}
    expire = datetime.utcnow() + timedelta(minutes=10)
    to_encode["exp"] = expire
    to_encode["iat"] = datetime.utcnow()
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_reset_token(token: str) -> int:
    payload = decode_token(token)  
    if payload.get("purpose") != "password_reset":
        raise AppException("Invalid reset token", status_code=401)
    return int(payload["sub"])
