from typing import Literal

from fastapi import APIRouter, Depends, Path, Query, status

from app.core.dependencies import get_current_user
from app.models.user_models import User
from app.schema.auth import MessageResponse
from app.schema.workshop import (
    AdminWorkshopCreateRequest,
    AdminWorkshopUpdateRequest,
    PaginatedWorkshopResponse,
    WorkshopResponse,
)
from app.service import workshop_service

router = APIRouter(prefix="/admin", tags=["Admin"])

ADMIN_ERRORS = {
    401: {"description": "Missing or invalid access token"},
    403: {"description": "Admin only"},
    404: {"description": "Not found"},
}


@router.post("/workshop-staff/{user_id}/approve", response_model=MessageResponse,
             summary="Approve a workshop staff registration", responses=ADMIN_ERRORS)
async def approve_staff(user_id: int = Path(..., gt=0), current_user: User = Depends(get_current_user)):
    return await workshop_service.approve_workshop_staff(current_user, user_id)


@router.post("/workshop-staff/{user_id}/reject", response_model=MessageResponse,
             summary="Reject a workshop staff registration", responses=ADMIN_ERRORS)
async def reject_staff(user_id: int = Path(..., gt=0), current_user: User = Depends(get_current_user)):
    return await workshop_service.reject_workshop_staff(current_user, user_id)


@router.get("/workshops", response_model=PaginatedWorkshopResponse,
            summary="List all workshops, any status", responses=ADMIN_ERRORS)
async def list_workshops(
    status_filter: Literal["pending", "approved", "rejected", "suspended"] | None = Query(None, alias="status"),
    q: str | None = Query(None, min_length=1, max_length=100, description="Match on workshop name"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    return await workshop_service.admin_list_workshops(current_user, status_filter, q, page, page_size)


@router.post("/workshops", response_model=WorkshopResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a workshop", responses=ADMIN_ERRORS)
async def create_workshop(data: AdminWorkshopCreateRequest, current_user: User = Depends(get_current_user)):
    return await workshop_service.admin_create_workshop(current_user, data)


@router.get("/workshops/{workshop_id}", response_model=WorkshopResponse,
            summary="Get any workshop, any status", responses=ADMIN_ERRORS)
async def get_workshop(workshop_id: int = Path(..., gt=0), current_user: User = Depends(get_current_user)):
    return await workshop_service.admin_get_workshop(current_user, workshop_id)


@router.put("/workshops/{workshop_id}", response_model=WorkshopResponse,
            summary="Update a workshop, including its status", responses=ADMIN_ERRORS)
async def update_workshop(
    data: AdminWorkshopUpdateRequest, workshop_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
):
    return await workshop_service.admin_update_workshop(current_user, workshop_id, data)


@router.delete("/workshops/{workshop_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a workshop that has no related records",
               responses={**ADMIN_ERRORS, 409: {"description": "Workshop has related records; suspend it instead"}})
async def delete_workshop(workshop_id: int = Path(..., gt=0), current_user: User = Depends(get_current_user)):
    await workshop_service.admin_delete_workshop(current_user, workshop_id)
