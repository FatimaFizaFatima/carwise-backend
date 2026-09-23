from datetime import date, timedelta
from fastapi import BackgroundTasks
from app.unit_of_work.unit_of_work import UnitOfWork
from app.core.exceptions import AppException
from app.core.roles import Role, BookingStatus, WorkshopStatus
from app.models.user_models import User
from app.models.booking import Booking, BookingItem
from app.schema.booking import BookingCreateRequest, BookingResponse, BookingItemResponse, RescheduleRequest
from app.utils.booking_reference import generate_booking_reference
from app.models.service_history import ServiceHistory
from app.service import notification_service


def _to_response(booking: Booking, items: list[BookingItem]) -> BookingResponse:
    return BookingResponse(
        id=booking.id, booking_reference=booking.booking_reference, user_id=booking.user_id,
        car_id=booking.car_id, workshop_id=booking.workshop_id, service_type=booking.service_type,
        pickup_address=booking.pickup_address, delivery_address=booking.delivery_address,
        note=booking.note, scheduled_date=booking.scheduled_date, scheduled_time=booking.scheduled_time,
        status=booking.status, total_price=booking.total_price, created_at=booking.created_at,
        items=[BookingItemResponse(workshop_service_id=i.workshop_service_id, price_snapshot=i.price_snapshot)
               for i in items],
    )


async def create_booking(current_user: User, data: BookingCreateRequest, background_tasks: BackgroundTasks) -> BookingResponse:
    async with UnitOfWork() as uow:
        car = await uow.cars.get_active_by_id(data.car_id)
        if car is None or car.user_id != current_user.id:
            raise AppException("Car not found or not yours", status_code=404)

        workshop = await uow.workshops.get_by_id(data.workshop_id)
        if workshop is None or workshop.status != WorkshopStatus.APPROVED:
            raise AppException("Workshop not found", status_code=404)

        if workshop.opens_at and workshop.closes_at:
            if not (workshop.opens_at <= data.scheduled_time <= workshop.closes_at):
                raise AppException("Selected time is outside workshop working hours", status_code=400)

        total_price = 0.0
        item_rows = []
        for service_id in data.workshop_service_ids:
            service = await uow.workshop_services.get_by_id(service_id)
            if service is None or service.workshop_id != data.workshop_id:
                raise AppException(f"Service {service_id} not found at this workshop", status_code=404)
            total_price += service.price
            item_rows.append((service_id, service.price))

        booking = Booking(
            booking_reference=generate_booking_reference(), user_id=current_user.id, car_id=data.car_id,
            workshop_id=data.workshop_id, service_type=data.service_type,
            pickup_address=data.pickup_address, delivery_address=data.delivery_address, note=data.note,
            scheduled_date=data.scheduled_date, scheduled_time=data.scheduled_time,
            status=BookingStatus.PENDING, total_price=total_price,
        )
        uow.bookings.add(booking)
        await uow.session.flush()

        items = []
        for service_id, price in item_rows:
            item = BookingItem(booking_id=booking.id, workshop_service_id=service_id, price_snapshot=price)
            uow.booking_items.add(item)
            items.append(item)

        await uow.commit()
        background_tasks.add_task(notification_service.notify_booking_created, booking)
        return _to_response(booking, items)
    

async def get_booking(current_user : User, booking_id : int) -> BookingResponse:
    async with UnitOfWork() as uow:
        booking = await uow.bookings.get_by_id(booking_id)
        if booking is None:
            raise AppException("Booking not found", status_code=404)

        if current_user.role == Role.CUSTOMER and booking.user_id != current_user.id:
            raise AppException("Not authorized to view this booking", status_code=403)
        if current_user.role == Role.WORKSHOP_STAFF and booking.workshop_id != current_user.workshop_id:
            raise AppException("Not authorized to view this booking", status_code=403)

        items = await uow.booking_items.get_by_booking(booking_id)
        return _to_response(booking, items)



async def list_my_bookings(current_user: User) -> list[BookingResponse]:
    async with UnitOfWork() as uow:
        if current_user.role == Role.CUSTOMER:
            bookings = await uow.bookings.get_by_user(current_user.id)
        elif current_user.role == Role.WORKSHOP_STAFF:
            if current_user.workshop_id is None:
                raise AppException("No workshop associated with this account", status_code=403)
            bookings = await uow.bookings.get_by_workshop(current_user.workshop_id)
        else:
            bookings = await uow.bookings.get_all()  

        result = []
        for b in bookings:
            items = await uow.booking_items.get_by_booking(b.id)
            result.append(_to_response(b, items))
        return result


async def cancel_booking(current_user: User, booking_id: int, background_tasks: BackgroundTasks) -> BookingResponse:
    async with UnitOfWork() as uow:
        booking = await uow.bookings.get_by_id(booking_id)
        if booking is None:
            raise AppException("Booking not found", status_code=404)
        if current_user.role == Role.CUSTOMER and booking.user_id != current_user.id:
            raise AppException("Not authorized", status_code=403)
        if current_user.role == Role.WORKSHOP_STAFF and booking.workshop_id != current_user.workshop_id:
            raise AppException("Not authorized", status_code=403)

        if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
            raise AppException("Booking can no longer be cancelled", status_code=400)

        await uow.bookings.update(booking, {"status": BookingStatus.CANCELLED})
        await uow.commit()
        background_tasks.add_task(notification_service.notify_booking_cancelled, booking)
        items = await uow.booking_items.get_by_booking(booking_id)
        return _to_response(booking, items)


async def reschedule_booking(current_user: User, booking_id: int, data: RescheduleRequest, background_tasks: BackgroundTasks) -> BookingResponse:
    async with UnitOfWork() as uow:
        booking = await uow.bookings.get_by_id(booking_id)
        if booking is None:
            raise AppException("Booking not found", status_code=404)
        if current_user.role == Role.CUSTOMER and booking.user_id != current_user.id:
            raise AppException("Not authorized", status_code=403)
        if current_user.role == Role.WORKSHOP_STAFF and booking.workshop_id != current_user.workshop_id:
            raise AppException("Not authorized", status_code=403)

        if booking.status not in (BookingStatus.PENDING, BookingStatus.CONFIRMED):
            raise AppException("Booking can no longer be rescheduled", status_code=400)

        workshop = await uow.workshops.get_by_id(booking.workshop_id)
        if workshop.opens_at and workshop.closes_at:
            if not (workshop.opens_at <= data.scheduled_time <= workshop.closes_at):
                raise AppException("Selected time is outside workshop working hours", status_code=400)

        old_date, old_time = booking.scheduled_date, booking.scheduled_time
        await uow.bookings.update(booking, {
            "scheduled_date": data.scheduled_date, "scheduled_time": data.scheduled_time,
        })
        await uow.commit()
        background_tasks.add_task(notification_service.notify_booking_rescheduled, booking, old_date, old_time)
        items = await uow.booking_items.get_by_booking(booking_id)
        return _to_response(booking, items)


VALID_TRANSITIONS = {
    BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED: {BookingStatus.IN_PROGRESS, BookingStatus.CANCELLED},
    BookingStatus.IN_PROGRESS: {BookingStatus.COMPLETED},
}


async def update_booking_status(current_user: User, booking_id: int, new_status: str, background_tasks: BackgroundTasks) -> BookingResponse:
    if current_user.role == Role.CUSTOMER:
        raise AppException("Not authorized to update booking status", status_code=403)

    async with UnitOfWork() as uow:
        booking = await uow.bookings.get_by_id(booking_id)
        if booking is None:
            raise AppException("Booking not found", status_code=404)
        if current_user.role == Role.WORKSHOP_STAFF and booking.workshop_id != current_user.workshop_id:
            raise AppException("Not authorized", status_code=403)

        allowed = VALID_TRANSITIONS.get(booking.status, set())
        if new_status not in allowed:
            raise AppException(f"Cannot move booking from {booking.status} to {new_status}", status_code=400)

        await uow.bookings.update(booking, {"status": new_status})
        await uow.commit()
        items = await uow.booking_items.get_by_booking(booking_id)

    if new_status == BookingStatus.CONFIRMED:
        background_tasks.add_task(notification_service.notify_booking_confirmed, booking)
    elif new_status == BookingStatus.CANCELLED:
        background_tasks.add_task(notification_service.notify_booking_cancelled, booking)
    else:
        background_tasks.add_task(notification_service.notify_booking_status_updated, booking, new_status)

    if new_status == BookingStatus.COMPLETED:
        async with UnitOfWork() as uow2:
            workshop = await uow2.workshops.get_by_id(booking.workshop_id)
            history = ServiceHistory(
                car_id=booking.car_id, booking_id=booking.id,
                title=f"Service at {workshop.workshop_name}", cost=booking.total_price,
                workshop_name=workshop.workshop_name, service_date=booking.scheduled_date,
            )
            uow2.service_history.add(history)
            await uow2.commit()

    return _to_response(booking, items)