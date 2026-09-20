from app.unit_of_work.unit_of_work import UnitOfWork
from app.core.exceptions import AppException
from app.core.securtiy import hash_password
from app.core.roles import Role, AccountStatus, WorkshopStatus
from app.models.user_models import User
from app.models.workshop import Workshop
from app.schema.workshop import WorkshopStaffRegisterRequest, WorkshopStaffRegisterResponse
from app.schema.auth import MessageResponse

from math import isfinite
from app.schema.workshop import WorkshopUpdateRequest, WorkshopResponse, WorkshopNearbyResponse, PaginatedWorkshopResponse
from app.schema.workshop_service import WorkshopServiceCreateRequest, WorkshopServiceResponse
from app.models.workshop_service import WorkshopService
from app.utils.file_storage import save_image
from fastapi import UploadFile


def _workshop_to_response(w: Workshop) -> WorkshopResponse:
    return WorkshopResponse(
        id=w.id, workshop_name=w.workshop_name, status=w.status, description=w.description,
        address=w.address, latitude=w.latitude, longitude=w.longitude, phone=w.phone,
        image_url=w.image_url, avg_rating=w.avg_rating, opens_at=w.opens_at, closes_at=w.closes_at,
    )


async def register_workshop_staff(data: WorkshopStaffRegisterRequest) -> WorkshopStaffRegisterResponse:
    async with UnitOfWork() as uow:
        if await uow.users.exists_by_email_or_phone(data.email, data.phone):
            raise AppException("Email or phone already exists", status_code=409)

        workshop = Workshop(workshop_name=data.workshop_name, status=WorkshopStatus.PENDING)
        uow.workshops.add(workshop)
        await uow.session.flush()

        staff = User(
            full_name=data.full_name, email=data.email, phone=data.phone,
            password_hash=hash_password(data.password), role=Role.WORKSHOP_STAFF,
            status=AccountStatus.PENDING_APPROVAL, workshop_id=workshop.id,
            email_verified=True,
        )
        uow.users.add(staff)
        await uow.commit()

        return WorkshopStaffRegisterResponse(
            id=staff.id, full_name=staff.full_name, email=staff.email,
            workshop_id=workshop.id, status=staff.status,
        )


async def approve_workshop_staff(current_user: User, user_id: int) -> MessageResponse:
    if current_user.role != Role.ADMIN:
        raise AppException("Only admin can approve workshop staff", status_code=403)

    async with UnitOfWork() as uow:
        staff = await uow.users.get_by_id(user_id)
        if staff is None or staff.role != Role.WORKSHOP_STAFF:
            raise AppException("Workshop staff account not found", status_code=404)
        if staff.status == AccountStatus.ACTIVE:
            raise AppException("This workshop staff account is already active", status_code=400)


        await uow.users.update(staff, {"status": AccountStatus.ACTIVE})

        if staff.workshop_id is not None:
            workshop = await uow.workshops.get_by_id(staff.workshop_id)
            if workshop is not None:
                await uow.workshops.update(workshop, {"status": WorkshopStatus.APPROVED})

        await uow.commit()
        return MessageResponse(message="Workshop staff approved.")


async def reject_workshop_staff(current_user: User, user_id: int) -> MessageResponse:
    if current_user.role != Role.ADMIN:
        raise AppException("Only admin can reject workshop staff", status_code=403)

    async with UnitOfWork() as uow:
        staff = await uow.users.get_by_id(user_id)
        if staff is None or staff.role != Role.WORKSHOP_STAFF:
            raise AppException("Workshop staff account not found", status_code=404)
        if staff.status == AccountStatus.ACTIVE:
            raise AppException("This workshop staff account is already rejected", status_code=400)


        await uow.users.update(staff, {"status": AccountStatus.REJECTED})

        if staff.workshop_id is not None:
            workshop = await uow.workshops.get_by_id(staff.workshop_id)
            if workshop is not None:
                await uow.workshops.update(workshop, {"status": WorkshopStatus.REJECTED})

        await uow.commit()
        return MessageResponse(message="Workshop staff registration rejected.")




async def get_my_workshop(current_user: User) -> WorkshopResponse:
    if current_user.role != Role.WORKSHOP_STAFF or current_user.workshop_id is None:
        raise AppException("No workshop associated with this account", status_code=404)

    async with UnitOfWork() as uow:
        workshop = await uow.workshops.get_by_id(current_user.workshop_id)
        if workshop is None:
            raise AppException("Workshop not found", status_code=404)
        return _workshop_to_response(workshop)


async def update_my_workshop(current_user: User, data: WorkshopUpdateRequest) -> WorkshopResponse:
    if current_user.role != Role.WORKSHOP_STAFF or current_user.workshop_id is None:
        raise AppException("No workshop associated with this account", status_code=403)

    async with UnitOfWork() as uow:
        workshop = await uow.workshops.get_by_id(current_user.workshop_id)
        if workshop is None:
            raise AppException("Workshop not found", status_code=404)

        await uow.workshops.update(workshop, data.model_dump(exclude_unset=True))
        await uow.commit()
        return _workshop_to_response(workshop)


async def get_workshop_detail(workshop_id: int) -> WorkshopResponse:
    async with UnitOfWork() as uow:
        workshop = await uow.workshops.get_by_id(workshop_id)
        if workshop is None or workshop.status != WorkshopStatus.APPROVED:
            raise AppException("Workshop not found", status_code=404)
        return _workshop_to_response(workshop)


async def search_workshops(category_id, min_price, max_price, sort_by, page, page_size) -> PaginatedWorkshopResponse:
    async with UnitOfWork() as uow:
        workshops = await uow.workshops.search(
            category_id=category_id, min_price=min_price, max_price=max_price,
            sort_by=sort_by, limit=page_size, offset=(page - 1) * page_size,
        )
        total = await uow.workshops.count_search(category_id, min_price, max_price)
        return PaginatedWorkshopResponse(
            items=[_workshop_to_response(w) for w in workshops],
            total=total, page=page, page_size=page_size,
            total_pages=(total + page_size - 1) // page_size,
        )


async def nearby_workshops(lat: float, lng: float, radius_km: float, page: int, page_size: int
                            ) -> list[WorkshopNearbyResponse]:
    if not (isfinite(lat) and isfinite(lng)):
        raise AppException("Invalid coordinates", status_code=400)

    async with UnitOfWork() as uow:
        rows = await uow.workshops.search_nearby(
            lat, lng, radius_km, limit=page_size, offset=(page - 1) * page_size
        )
        return [
            WorkshopNearbyResponse(**_workshop_to_response(w).model_dump(), distance_km=round(d, 2))
            for w, d in rows
        ]


async def add_service(current_user: User, data: WorkshopServiceCreateRequest) -> WorkshopServiceResponse:
    if current_user.role != Role.WORKSHOP_STAFF or current_user.workshop_id is None:
        raise AppException("No workshop associated with this account", status_code=403)

    async with UnitOfWork() as uow:
        category = await uow.service_categories.get_by_id(data.category_id)
        if category is None:
            raise AppException("Service category not found", status_code=404)

        if await uow.workshop_services.exists_for_workshop(current_user.workshop_id, data.category_id):
            raise AppException("This service is already listed for your workshop", status_code=409)

        service = WorkshopService(
            workshop_id=current_user.workshop_id, category_id=data.category_id, price=data.price
        )
        uow.workshop_services.add(service)
        await uow.commit()
        return WorkshopServiceResponse(
            id=service.id, workshop_id=service.workshop_id,
            category_id=service.category_id, price=service.price,
        )


async def list_workshop_services(workshop_id: int) -> list[WorkshopServiceResponse]:
    async with UnitOfWork() as uow:
        services = await uow.workshop_services.get_by_workshop(workshop_id)
        return [
            WorkshopServiceResponse(id=s.id, workshop_id=s.workshop_id,
                                     category_id=s.category_id, price=s.price)
            for s in services
        ]


async def remove_service(current_user: User, service_id: int) -> None:
    async with UnitOfWork() as uow:
        service = await uow.workshop_services.get_by_id(service_id)
        if service is None:
            raise AppException("Service not found", status_code=404)

        if current_user.role == Role.WORKSHOP_STAFF and service.workshop_id != current_user.workshop_id:
            raise AppException("Not authorized to remove this service", status_code=403)
        if current_user.role == Role.CUSTOMER:
            raise AppException("Not authorized", status_code=403)

        await uow.workshop_services.delete(service)
        await uow.commit()    


async def upload_workshop_image(current_user: User, file: UploadFile) -> WorkshopResponse:
    if current_user.role != Role.WORKSHOP_STAFF or current_user.workshop_id is None:
        raise AppException("No workshop associated with this account", status_code=403)

    image_url = await save_image(file, "workshops")

    async with UnitOfWork() as uow:
        workshop = await uow.workshops.get_by_id(current_user.workshop_id)
        await uow.workshops.update(workshop, {"image_url": image_url})
        await uow.commit()
        return _workshop_to_response(workshop)
