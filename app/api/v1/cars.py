from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user
from app.models.user_models import User
from app.schema.car import CarCreateRequest, CarUpdateRequest, CarResponse, AssociateCarRequest
from app.service import car_service

router = APIRouter(prefix="/cars", tags=["Cars"])


@router.post("", response_model=CarResponse, status_code=status.HTTP_201_CREATED)
async def create_car(data: CarCreateRequest, current_user: User = Depends(get_current_user)):
    return await car_service.create_car(current_user, data)


@router.get("", response_model=list[CarResponse])
async def list_cars(
    target_user_id: int | None = Query(None, description="Required for staff/admin"),
    current_user: User = Depends(get_current_user),
):
    return await car_service.list_cars(current_user, target_user_id)


@router.get("/{car_id}", response_model=CarResponse)
async def get_car(car_id: int, current_user: User = Depends(get_current_user)):
    return await car_service.get_car(current_user, car_id)


@router.put("/{car_id}", response_model=CarResponse)
async def update_car(car_id: int, data: CarUpdateRequest, current_user: User = Depends(get_current_user)):
    return await car_service.update_car(current_user, car_id, data)


@router.post("/{car_id}/associate", response_model=CarResponse)
async def associate_car(
    car_id: int, data: AssociateCarRequest, current_user: User = Depends(get_current_user)
):
    return await car_service.associate_car(current_user, car_id, data)

@router.delete("/{car_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_car(car_id: int, current_user: User = Depends(get_current_user)):
    await car_service.delete_car(current_user, car_id)


@router.post("/{car_id}/restore", response_model=CarResponse)
async def restore_car(car_id: int, current_user: User = Depends(get_current_user)):
    return await car_service.restore_car(current_user, car_id)
