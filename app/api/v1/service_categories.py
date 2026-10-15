from fastapi import APIRouter, Depends, Path, status

from app.core.dependencies import get_current_user
from app.models.user_models import User
from app.schema.service_category import (
    ServiceCategoryCreateRequest,
    ServiceCategoryResponse,
    ServiceCategoryUpdateRequest,
)
from app.service import service_category_service

router = APIRouter(prefix="/service-categories", tags=["Service Categories"])

ADMIN_ERRORS = {
    401: {"description": "Missing or invalid access token"},
    403: {"description": "Admin only"},
    404: {"description": "Category not found"},
    409: {"description": "Duplicate name, or category in use"},
}


@router.get("", response_model=list[ServiceCategoryResponse], summary="List service categories")
async def list_categories():
    return await service_category_service.list_categories()


@router.get("/{category_id}", response_model=ServiceCategoryResponse, summary="Get a service category")
async def get_category(category_id: int = Path(..., gt=0)):
    return await service_category_service.get_category(category_id)


@router.post(
    "", response_model=ServiceCategoryResponse, status_code=status.HTTP_201_CREATED,
    summary="Create a service category (admin)", responses=ADMIN_ERRORS,
)
async def create_category(data: ServiceCategoryCreateRequest, current_user: User = Depends(get_current_user)):
    return await service_category_service.create_category(current_user, data)


@router.put(
    "/{category_id}", response_model=ServiceCategoryResponse,
    summary="Update a service category (admin)", responses=ADMIN_ERRORS,
)
async def update_category(
    data: ServiceCategoryUpdateRequest, category_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
):
    return await service_category_service.update_category(current_user, category_id, data)


@router.delete(
    "/{category_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a service category (admin)", responses=ADMIN_ERRORS,
)
async def delete_category(category_id: int = Path(..., gt=0), current_user: User = Depends(get_current_user)):
    await service_category_service.delete_category(current_user, category_id)
