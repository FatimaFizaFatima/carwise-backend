from app.unit_of_work.unit_of_work import UnitOfWork
from app.core.exceptions import AppException
from app.models.cars import Car
from app.models.user_models import User
from app.schema.car import CarCreateRequest, CarUpdateRequest, CarResponse, AssociateCarRequest
from app.core.roles import Role
from datetime import datetime, timezone


def _to_response(car: Car) -> CarResponse:
    return CarResponse(
        id=car.id, user_id=car.user_id, registration_no=car.registration_no,
        owner_name=car.owner_name, make=car.make, vehicle_model=car.vehicle_model,
        model_year=car.model_year, registration_date=car.registration_date,
        provision=car.provision, body_type=car.body_type, class_of_vehicle=car.class_of_vehicle,
        engine_number=car.engine_number, engine_capacity_cc=car.engine_capacity_cc,
        seating_capacity=car.seating_capacity, created_at=car.created_at,
    )


async def create_car(current_user: User, data: CarCreateRequest) -> CarResponse:
    if current_user.role == Role.WORKSHOP_STAFF:
        raise AppException("Workshop staff cannot add cars directly", status_code=403)

    async with UnitOfWork() as uow:
        if await uow.cars.exists_by_registration_or_engine(data.registration_no, data.engine_number):
            raise AppException("A car with this registration or engine number already exists",
                                status_code=409)

        owner_id = current_user.id
        if data.user_id is not None:
            if current_user.role != Role.ADMIN:
                raise AppException("You cannot assign a car to another user", status_code=403)
            owner_id = data.user_id

        car = Car(
            user_id=owner_id, registration_no=data.registration_no, owner_name=data.owner_name,
            make=data.make, vehicle_model=data.vehicle_model, model_year=data.model_year,
            registration_date=data.registration_date, provision=data.provision,
            body_type=data.body_type, class_of_vehicle=data.class_of_vehicle,
            engine_number=data.engine_number, engine_capacity_cc=data.engine_capacity_cc,
            seating_capacity=data.seating_capacity,
        )
        uow.cars.add(car)
        await uow.commit()
        return _to_response(car)


async def list_cars(current_user: User, target_user_id: int | None) -> list[CarResponse]:
    async with UnitOfWork() as uow:
        if current_user.role == Role.CUSTOMER:
            user_id = current_user.id
        else:
            if target_user_id is None:
                raise AppException("target_user_id is required for staff/admin", status_code=400)
            user_id = target_user_id

        cars = await uow.cars.get_by_user(user_id)
        return [_to_response(c) for c in cars]


async def get_car(current_user: User, car_id: int) -> CarResponse:
    async with UnitOfWork() as uow:
        car = await uow.cars.get_active_by_id(car_id)
        if car is None:
            raise AppException("Car not found", status_code=404)
        if current_user.role == "customer" and car.user_id != current_user.id:
            raise AppException("Not authorized to view this car", status_code=403)
        return _to_response(car)


async def update_car(current_user: User, car_id: int, data: CarUpdateRequest) -> CarResponse:
    async with UnitOfWork() as uow:
        car = await uow.cars.get_active_by_id(car_id)
        if car is None:
            raise AppException("Car not found", status_code=404)
        if current_user.role == "customer" and car.user_id != current_user.id:
            raise AppException("Not authorized to update this car", status_code=403)

        await uow.cars.update(car, data.model_dump(exclude_unset=True))
        await uow.commit()
        return _to_response(car)


async def associate_car(current_user: User, car_id: int, data: AssociateCarRequest) -> CarResponse:
    if current_user.role not in ("workshop_staff", "admin"):
        raise AppException("Not authorized to associate cars", status_code=403)

    async with UnitOfWork() as uow:
        car = await uow.cars.get_active_by_id(car_id)
        if car is None:
            raise AppException("Car not found", status_code=404)

        target_user = await uow.users.get_by_id(data.user_id)
        if target_user is None:
            raise AppException("Target user not found", status_code=404)

        await uow.cars.update(car, {"user_id": data.user_id})
        await uow.commit()
        return _to_response(car)


async def delete_car(current_user: User, car_id: int) -> None:
    async with UnitOfWork() as uow:
        car = await uow.cars.get_active_by_id(car_id)
        if car is None:
            raise AppException("Car not found", status_code=404)

        if current_user.role == Role.CUSTOMER and car.user_id != current_user.id:
            raise AppException("Not authorized to delete this car", status_code=403)
        if current_user.role == Role.WORKSHOP_STAFF:
            raise AppException("Workshop staff cannot delete cars", status_code=403)

        await uow.cars.update(car, {"deleted_at": datetime.now(timezone.utc)})
        await uow.commit()

async def restore_car(current_user: User, car_id: int) -> CarResponse:
    async with UnitOfWork() as uow:
        car = await uow.cars.get_by_id(car_id)
        if car is None or car.deleted_at is None:
            raise AppException("Car not found or not deleted", status_code=404)

        if current_user.role == Role.CUSTOMER and car.user_id != current_user.id:
            raise AppException("Not authorized to restore this car", status_code=403)

        conflict = await uow.cars.exists_by_registration_or_engine(car.registration_no, car.engine_number)
        if conflict:
            raise AppException(
                "Cannot restore: this registration/engine number is now in use by another active car",
                status_code=409,
            )

        await uow.cars.update(car, {"deleted_at": None})
        await uow.commit()
        return _to_response(car)    