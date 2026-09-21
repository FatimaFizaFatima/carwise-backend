from fastapi import APIRouter, Depends, status
from app.core.dependencies import get_current_user
from app.service import booking_service
from app.schema.booking import BookingResponse, BookingCreateRequest, BookingItemResponse, BookingStatusUpdateRequest, RescheduleRequest
from app.models.user_models import User

router = APIRouter(prefix="/booking", tags=["Booking"])

@router.post("", response_model=BookingResponse, status_code=status.HTTP_201_CREATED)
async def create_booking(data : BookingCreateRequest, current_user : User = Depends(get_current_user)):
    return await booking_service.create_booking(current_user, data)

@router.get("", response_model=list[BookingResponse])
async def list_my_bookings(current_user : User = Depends(get_current_user)):
    return await booking_service.list_my_bookings(current_user)

@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(booking_id : int, current_user : User = Depends(get_current_user)):
    return await booking_service.get_booking(current_user, booking_id)

@router.post("/{booking_id}/cancel", response_model=BookingResponse)
async def cancel_booking(booking_id : int, current_user : User = Depends(get_current_user)):
    return await booking_service.cancel_booking(current_user, booking_id)    


@router.post("/{booking_id}/reschedule", response_model=BookingResponse)
async def reschedule_booking(booking_id: int, data: RescheduleRequest, current_user: User = Depends(get_current_user)):
    return await booking_service.reschedule_booking(current_user, booking_id, data)


@router.patch("/{booking_id}/status", response_model=BookingResponse)
async def update_status(booking_id: int, data: BookingStatusUpdateRequest, current_user: User = Depends(get_current_user)):
    return await booking_service.update_booking_status(current_user, booking_id, data.status)
