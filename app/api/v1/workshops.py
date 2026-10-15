from typing import Literal

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile, status

from app.core.dependencies import get_current_user
from app.models.user_models import User
from app.schema.workshop import (
    PaginatedWorkshopResponse,
    WorkshopDetailResponse,
    WorkshopNearbyResponse,
    WorkshopResponse,
    WorkshopUpdateRequest,
)
from app.schema.workshop_review import ReviewCreateRequest, ReviewResponse
from app.schema.workshop_service import (
    WorkshopServiceCreateRequest,
    WorkshopServiceResponse,
    WorkshopServiceUpdateRequest,
)
from app.service import workshop_review_service, workshop_service

router = APIRouter(prefix="/workshops", tags=["Workshops"])

AUTH_ERRORS = {
    401: {"description": "Missing or invalid access token"},
    403: {"description": "Account inactive or role not allowed"},
    404: {"description": "Resource not found"},
}


@router.get("/me", response_model=WorkshopResponse, summary="Get my workshop (staff)", responses=AUTH_ERRORS)
async def get_my_workshop(current_user: User = Depends(get_current_user)):
    return await workshop_service.get_my_workshop(current_user)


@router.put("/me", response_model=WorkshopResponse, summary="Update my workshop (staff)", responses=AUTH_ERRORS)
async def update_my_workshop(data: WorkshopUpdateRequest, current_user: User = Depends(get_current_user)):
    return await workshop_service.update_my_workshop(current_user, data)


@router.post("/me/image", response_model=WorkshopResponse, summary="Upload workshop image (staff)", responses=AUTH_ERRORS)
async def upload_workshop_image(file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    return await workshop_service.upload_workshop_image(current_user, file)


@router.post(
    "/me/services", response_model=WorkshopServiceResponse, status_code=status.HTTP_201_CREATED,
    summary="Add a service with price (staff)", responses={**AUTH_ERRORS, 409: {"description": "Service already listed"}},
)
async def add_service(data: WorkshopServiceCreateRequest, current_user: User = Depends(get_current_user)):
    return await workshop_service.add_service(current_user, data)


@router.put(
    "/me/services/{service_id}", response_model=WorkshopServiceResponse,
    summary="Update a service price (staff/admin)", responses=AUTH_ERRORS,
)
async def update_service(
    data: WorkshopServiceUpdateRequest, service_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
):
    return await workshop_service.update_service(current_user, service_id, data)


@router.delete(
    "/me/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a service (staff/admin)",
    responses={**AUTH_ERRORS, 409: {"description": "Service is used by existing bookings"}},
)
async def remove_service(service_id: int = Path(..., gt=0), current_user: User = Depends(get_current_user)):
    await workshop_service.remove_service(current_user, service_id)


@router.get("/search", response_model=PaginatedWorkshopResponse, summary="Search and filter approved workshops")
async def search_workshops(
    q: str | None = Query(None, min_length=1, max_length=100, description="Match on workshop name"),
    category_id: int | None = Query(None, gt=0),
    min_price: float | None = Query(None, ge=0, le=1_000_000),
    max_price: float | None = Query(None, ge=0, le=1_000_000),
    min_rating: float | None = Query(None, ge=0, le=5),
    sort_by: Literal["name", "rating"] = "name",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return await workshop_service.search_workshops(
        q, category_id, min_price, max_price, min_rating, sort_by, page, page_size
    )


@router.get("/nearby", response_model=list[WorkshopNearbyResponse], summary="Approved workshops near a location, with distance")
async def nearby_workshops(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, gt=0, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return await workshop_service.nearby_workshops(lat, lng, radius_km, page, page_size)


@router.get("/{workshop_id}", response_model=WorkshopDetailResponse, summary="Workshop details with services")
async def get_workshop_detail(workshop_id: int = Path(..., gt=0)):
    return await workshop_service.get_workshop_detail(workshop_id)


@router.get("/{workshop_id}/services", response_model=list[WorkshopServiceResponse], summary="List a workshop's services and prices")
async def list_workshop_services(workshop_id: int = Path(..., gt=0)):
    return await workshop_service.list_workshop_services(workshop_id)

@router.post(
    "/{workshop_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED,
    summary="Review a workshop (customer, completed booking only)",
    responses={**AUTH_ERRORS, 409: {"description": "Booking already reviewed"}},
)
async def create_review(
    data: ReviewCreateRequest, workshop_id: int = Path(..., gt=0),
    current_user: User = Depends(get_current_user),
):
    return await workshop_review_service.create_review(current_user, workshop_id, data)


@router.get("/{workshop_id}/reviews", response_model=list[ReviewResponse], summary="List reviews, newest first")
async def list_reviews(
    workshop_id: int = Path(..., gt=0),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return await workshop_review_service.list_reviews(workshop_id, page, page_size)
