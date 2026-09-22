from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user
from app.schema.service_history import AddExpenseRequest, ServiceHistoryResponse
from app.service import service_history_service

router = APIRouter(prefix="/history", tags=["Service History"])


@router.post("", response_model=ServiceHistoryResponse, status_code=status.HTTP_201_CREATED)
async def add_expense(data: AddExpenseRequest, current_user=Depends(get_current_user)):
    return await service_history_service.add_expense(current_user, data)


@router.get("/services", response_model=list[ServiceHistoryResponse])
async def get_my_service_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                                  current_user=Depends(get_current_user)):
    return await service_history_service.get_my_service_history(current_user, page, page_size)


@router.get("/expenses", response_model=list[ServiceHistoryResponse])
async def get_my_expense_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                                  current_user=Depends(get_current_user)):
    return await service_history_service.get_my_expense_history(current_user, page, page_size)


@router.get("/workshop", response_model=list[ServiceHistoryResponse])
async def get_workshop_history(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                                current_user=Depends(get_current_user)):
    return await service_history_service.get_workshop_history(current_user, page, page_size)


@router.get("/car/{car_id}", response_model=list[ServiceHistoryResponse])
async def get_car_history(car_id: int, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                           current_user=Depends(get_current_user)):
    return await service_history_service.get_car_history(current_user, car_id, page, page_size)


@router.get("/{history_id}", response_model=ServiceHistoryResponse)
async def get_history_detail(history_id: int, current_user=Depends(get_current_user)):
    return await service_history_service.get_history_detail(current_user, history_id)