from app.core.roles import Role
from app.unit_of_work.unit_of_work import UnitOfWork
from app.core.exceptions import AppException
from app.models.service_history import ServiceHistory
from app.schema.service_history import AddExpenseRequest, ServiceHistoryResponse


def _to_response(h: ServiceHistory) -> ServiceHistoryResponse:
    return ServiceHistoryResponse(
        id=h.id, car_id=h.car_id, booking_id=h.booking_id, title=h.title, cost=h.cost,
        service_details=h.service_details, workshop_name=h.workshop_name,
        attachment_url=h.attachment_url, service_date=h.service_date, created_at=h.created_at,
        is_manual=h.booking_id is None,
    )


async def add_expense(current_user, data: AddExpenseRequest) -> ServiceHistoryResponse:
    async with UnitOfWork() as uow:
        car = await uow.cars.get_active_by_id(data.car_id)
        if car is None or car.user_id != current_user.id:
            raise AppException("Car not found or not yours", status_code=404)

        entry = ServiceHistory(
            car_id=data.car_id, booking_id=None, title=data.title, cost=data.cost,
            service_details=data.service_details, workshop_name=data.workshop_name,
            service_date=data.service_date,
        )
        uow.service_history.add(entry)
        await uow.commit()
        return _to_response(entry)


async def _user_car_ids(uow, current_user) -> list[int]:
    cars = await uow.cars.get_by_user(current_user.id)
    return [c.id for c in cars]


async def get_my_service_history(current_user, page: int, page_size: int) -> list[ServiceHistoryResponse]:
    async with UnitOfWork() as uow:
        offset = (page - 1) * page_size
        if current_user.role == Role.ADMIN:
            entries = await uow.service_history.get_all(page_size, offset)
        else:
            car_ids = await _user_car_ids(uow, current_user)
            entries = (await uow.service_history.get_service_history_by_user_cars(car_ids, page_size, offset)
                       if car_ids else [])
        return [_to_response(e) for e in entries]


async def get_my_expense_history(current_user, page: int, page_size: int) -> list[ServiceHistoryResponse]:
    async with UnitOfWork() as uow:
        offset = (page - 1) * page_size
        if current_user.role == Role.ADMIN:
            entries = await uow.service_history.get_all(page_size, offset)
        else:
            car_ids = await _user_car_ids(uow, current_user)
            entries = (await uow.service_history.get_expense_history_by_user_cars(car_ids, page_size, offset)
                       if car_ids else [])
        return [_to_response(e) for e in entries]


async def get_workshop_history(current_user, page: int, page_size: int) -> list[ServiceHistoryResponse]:
    if current_user.role != Role.WORKSHOP_STAFF or current_user.workshop_id is None:
        raise AppException("No workshop associated with this account", status_code=403)

    async with UnitOfWork() as uow:
        entries = await uow.service_history.get_by_workshop(
            current_user.workshop_id, page_size, (page - 1) * page_size
        )
        return [_to_response(e) for e in entries]


async def get_car_history(current_user, car_id: int, page: int, page_size: int) -> list[ServiceHistoryResponse]:
    async with UnitOfWork() as uow:
        car = await uow.cars.get_active_by_id(car_id)
        if car is None:
            raise AppException("Car not found", status_code=404)
        if current_user.role == Role.CUSTOMER and car.user_id != current_user.id:
            raise AppException("Not authorized", status_code=403)
        if current_user.role == Role.WORKSHOP_STAFF:
            raise AppException("Use /history/workshop instead", status_code=403)

        entries = await uow.service_history.get_by_car(car_id, page_size, (page - 1) * page_size)
        return [_to_response(e) for e in entries]


async def get_history_detail(current_user, history_id: int) -> ServiceHistoryResponse:
    async with UnitOfWork() as uow:
        entry = await uow.service_history.get_by_id(history_id)
        if entry is None:
            raise AppException("History entry not found", status_code=404)

        car = await uow.cars.get_by_id(entry.car_id)
        if current_user.role == Role.CUSTOMER and (car is None or car.user_id != current_user.id):
            raise AppException("Not authorized", status_code=403)
        if current_user.role == Role.WORKSHOP_STAFF:
            if entry.booking_id is None:
                raise AppException("Not authorized", status_code=403)
            booking = await uow.bookings.get_by_id(entry.booking_id)
            if booking is None or booking.workshop_id != current_user.workshop_id:
                raise AppException("Not authorized", status_code=403)

        return _to_response(entry)