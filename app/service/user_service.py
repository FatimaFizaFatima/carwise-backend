from datetime import datetime, timezone
from app.unit_of_work import UnitOfWork
from app.core.securtiy import hash_password, verify_password
from app.core.exceptions import AppException
from app.schema.user import ChangePasswordRequest, UpdateProfileRequest, UserProfileResponse
from app.models.user_models import User
from app.utils.file_storage import save_avatar


async def get_profile(current_user: User) -> UserProfileResponse:
    return UserProfileResponse(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        phone=current_user.phone,
        location=current_user.location,
        email_verified=current_user.email_verified,
        phone_verified=current_user.phone_verified,
        avatar_url=current_user.avatar_url
        
    )


async def update_profile(current_user: User, data: UpdateProfileRequest) -> UserProfileResponse:
    async with UnitOfWork() as uow:
        update_data = data.model_dump(exclude_unset=True)

        if "phone" in update_data and update_data["phone"] != current_user.phone:
            existing = await uow.users.get_user_by_phone(update_data["phone"])
            if existing is not None and existing.id != current_user.id:
                raise AppException("Phone number already in use", status_code=409)

        user = await uow.users.get_by_id(current_user.id)
        await uow.users.update(user, update_data)
        await uow.commit()

        return await get_profile(user)


async def change_password(current_user: User, data: ChangePasswordRequest) -> None:
    async with UnitOfWork() as uow:
        user = await uow.users.get_by_id(current_user.id)

        if user.password_hash is None or not verify_password(data.old_password, user.password_hash):
            raise AppException("Old password is incorrect", status_code=401)

        await uow.users.update(user, {"password_hash": hash_password(data.new_password)})

        tokens = await uow.refresh_tokens.get_by_active_user(user.id)
        for token in tokens:
            token.revoked_at = datetime.now(timezone.utc)

        await uow.commit()


async def update_avatar(current_user, file) -> UserProfileResponse:
    avatar_url = await save_avatar(file)

    async with UnitOfWork() as uow:
        user = await uow.users.get_by_id(current_user.id)
        await uow.users.update(user, {"avatar_url": avatar_url})
        await uow.commit()
        return await get_profile(user)
        