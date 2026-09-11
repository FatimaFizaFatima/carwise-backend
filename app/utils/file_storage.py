import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.exceptions import AppException

AVATAR_DIR = Path("uploads/avatars")
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_BYTES = 5 * 1024 * 1024  


async def save_avatar(file: UploadFile) -> str:
    if file.content_type not in ALLOWED_TYPES:
        raise AppException("Only JPEG, PNG, or WebP images are allowed", status_code=400)

    contents = await file.read()
    if len(contents) > MAX_SIZE_BYTES:
        raise AppException("Image must be under 5MB", status_code=400)

    extension = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{extension}"
    filepath = AVATAR_DIR / filename

    with open(filepath, "wb") as f:
        f.write(contents)

    return f"/uploads/avatars/{filename}"