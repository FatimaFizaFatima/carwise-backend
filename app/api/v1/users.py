from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user
from app.models.user_models import User
from app.schema.user import ChangePasswordRequest, UpdateProfileRequest, UserProfileResponse
from app.schema.auth import MessageResponse
from app.service import user_service
from fastapi import UploadFile, File

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserProfileResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return await user_service.get_profile(current_user)


@router.put("/me", response_model=UserProfileResponse)
async def update_me(data: UpdateProfileRequest, current_user: User = Depends(get_current_user)):
    return await user_service.update_profile(current_user, data)


@router.put("/me/password", response_model=MessageResponse)
async def change_my_password(data: ChangePasswordRequest, current_user: User = Depends(get_current_user)):
    await user_service.change_password(current_user, data)
    return MessageResponse(message="Password updated successfully. Please log in again.")

@router.post("/me/avatar", response_model=UserProfileResponse)
async def upload_avatar(file: UploadFile = File(...),current_user: User = Depends(get_current_user)):
    return await user_service.update_avatar(current_user, file)
