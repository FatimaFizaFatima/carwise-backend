from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_user
from app.models.user_models import User
from app.schema.auth import MessageResponse
from app.service import workshop_service

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/workshop-staff/{user_id}/approve", response_model=MessageResponse)
async def approve_staff(user_id: int, current_user: User = Depends(get_current_user)):
    return await workshop_service.approve_workshop_staff(current_user, user_id)


@router.post("/workshop-staff/{user_id}/reject", response_model=MessageResponse)
async def reject_staff(user_id: int, current_user: User = Depends(get_current_user)):
    return await workshop_service.reject_workshop_staff(current_user, user_id)