from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from app.core.dependencies import get_current_user
from app.models.user_models import User
from app.schema.workshop import WorkshopUpdateRequest, WorkshopResponse, WorkshopNearbyResponse, PaginatedWorkshopResponse
from app.schema.workshop_service import WorkshopServiceCreateRequest, WorkshopServiceResponse
from app.service import workshop_service
from app.schema.workshop_review import ReviewCreateRequest, ReviewResponse
from app.service import workshop_review_service

router = APIRouter(prefix="/workshops", tags=["Workshops"])


@router.get("/me", response_model=WorkshopResponse)
async def get_my_workshop(current_user: User = Depends(get_current_user)):
    return await workshop_service.get_my_workshop(current_user)


@router.put("/me", response_model=WorkshopResponse)
async def update_my_workshop(data: WorkshopUpdateRequest, current_user: User = Depends(get_current_user)):
    return await workshop_service.update_my_workshop(current_user, data)


@router.get("/search", response_model=PaginatedWorkshopResponse)
async def search_workshops(
    category_id: int | None = None, min_price: float | None = None, max_price: float | None = None,
    sort_by: str = "name", page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    return await workshop_service.search_workshops(category_id, min_price, max_price, sort_by, page, page_size)


@router.get("/nearby", response_model=list[WorkshopNearbyResponse])
async def nearby_workshops(
    lat: float, lng: float, radius_km: float = Query(10, gt=0, le=100),
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
):
    return await workshop_service.nearby_workshops(lat, lng, radius_km, page, page_size)


@router.get("/{workshop_id}", response_model=WorkshopResponse)
async def get_workshop_detail(workshop_id: int):
    return await workshop_service.get_workshop_detail(workshop_id)


@router.get("/{workshop_id}/services", response_model=list[WorkshopServiceResponse])
async def list_workshop_services(workshop_id: int):
    return await workshop_service.list_workshop_services(workshop_id)


@router.post("/me/services", response_model=WorkshopServiceResponse, status_code=status.HTTP_201_CREATED)
async def add_service(data: WorkshopServiceCreateRequest, current_user: User = Depends(get_current_user)):
    return await workshop_service.add_service(current_user, data)


@router.delete("/me/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_service(service_id: int, current_user: User = Depends(get_current_user)):
    await workshop_service.remove_service(current_user, service_id)



@router.post("/me/image", response_model=WorkshopResponse)
async def upload_workshop_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    return await workshop_service.upload_workshop_image(current_user, file)


@router.post("/{workshop_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(workshop_id: int, data: ReviewCreateRequest, current_user: User = Depends(get_current_user)):
    return await workshop_review_service.create_review(current_user, workshop_id, data)


@router.get("/{workshop_id}/reviews", response_model=list[ReviewResponse])
async def list_reviews(workshop_id: int):
    return await workshop_review_service.list_reviews(workshop_id)