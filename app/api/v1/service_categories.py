from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user
from app.models.user_models import User
from app.schema.service_category import ServiceCategoryCreateRequest, ServiceCategoryResponse
from app.service import service_category_service

router = APIRouter(prefix="/service-categories", tags=["Service Categories"])


@router.get("", response_model=list[ServiceCategoryResponse])
async def list_categories():
    return await service_category_service.list_categories()


@router.post("", response_model=ServiceCategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(data: ServiceCategoryCreateRequest, current_user: User = Depends(get_current_user)):
    return await service_category_service.create_category(current_user, data)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, current_user: User = Depends(get_current_user)):
    await service_category_service.delete_category(current_user, category_id)