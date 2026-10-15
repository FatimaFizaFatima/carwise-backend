from fastapi import UploadFile
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import AppException
from app.core.roles import AccountStatus, Role, WorkshopStatus
from app.core.securtiy import hash_password
from app.models.user_models import User
from app.models.workshop import Workshop
from app.models.workshop_service import WorkshopService
from app.schema.auth import MessageResponse
from app.schema.workshop import (
    AdminWorkshopCreateRequest,
    AdminWorkshopUpdateRequest,
    PaginatedWorkshopResponse,
    WorkshopDetailResponse,
    WorkshopNearbyResponse,
    WorkshopResponse,
    WorkshopStaffRegisterRequest,
    WorkshopStaffRegisterResponse,
    WorkshopUpdateRequest,
)
from app.schema.workshop_service import (
    WorkshopServiceCreateRequest,
    WorkshopServiceResponse,
    WorkshopServiceUpdateRequest,
)
from app.unit_of_work.unit_of_work import UnitOfWork
from app.utils.file_storage import save_image


def _workshop_to_response(w: Workshop) -> WorkshopResponse:
    return WorkshopResponse(
        id=w.id, workshop_name=w.workshop_name, status=w.status, description=w.description,
        address=w.address, latitude=w.latitude, longitude=w.longitude, phone=w.phone,
        image_url=w.image_url, avg_rating=w.avg_rating, opens_at=w.opens_at, closes_at=w.closes_at,
    )


def _service_to_response(s: WorkshopService) -> WorkshopServiceResponse:
    return WorkshopServiceResponse(
        id=s.id, workshop_id=s.workshop_id, category_id=s.category_id, price=s.price,
    )


def _require_admin(current_user: User) -> None:
    if current_user.role != Role.ADMIN:
        raise AppException("Admin access required", status_code=403)


def _require_staff_workshop(current_user: User) -> int:
    if current_user.role != Role.WORKSHOP_STAFF or current_user.workshop_id is None:
        raise AppException("No workshop associated with this account", status_code=403)
    return current_user.workshop_id


async def get_approved_workshop(uow: UnitOfWork, workshop_id: int) -> Workshop:
    """Public-facing lookup: pending/rejected/suspended workshops are treated as not found."""
    workshop = await uow.workshops.get_by_id(workshop_id)
    if workshop is None or workshop.status != WorkshopStatus.APPROVED:
        raise AppException("Workshop not found", status_code=404)
    return workshop


def _total_pages(total: int, page_size: int) -> int:
    return (total + page_size - 1) // page_size

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
    _require_admin(current_user)

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
    _require_admin(current_user)

    async with UnitOfWork() as uow:
        staff = await uow.users.get_by_id(user_id)
        if staff is None or staff.role != Role.WORKSHOP_STAFF:
            raise AppException("Workshop staff account not found", status_code=404)
        if staff.status == AccountStatus.REJECTED:
            raise AppException("This workshop staff account is already rejected", status_code=400)
        if staff.status == AccountStatus.ACTIVE:
            raise AppException(
                "An active workshop staff account cannot be rejected. Suspend the workshop instead.",
                status_code=400,
            )

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
    workshop_id = _require_staff_workshop(current_user)

    async with UnitOfWork() as uow:
        workshop = await uow.workshops.get_by_id(workshop_id)
        if workshop is None:
            raise AppException("Workshop not found", status_code=404)

        changes = data.model_dump(exclude_unset=True)
        if changes.get("workshop_name") is None:
            changes.pop("workshop_name", None)  

        await uow.workshops.update(workshop, changes)
        await uow.commit()
        return _workshop_to_response(workshop)


async def upload_workshop_image(current_user: User, file: UploadFile) -> WorkshopResponse:
    workshop_id = _require_staff_workshop(current_user)

    image_url = await save_image(file, "workshops")

    async with UnitOfWork() as uow:
        workshop = await uow.workshops.get_by_id(workshop_id)
        if workshop is None:
            raise AppException("Workshop not found", status_code=404)
        await uow.workshops.update(workshop, {"image_url": image_url})
        await uow.commit()
        return _workshop_to_response(workshop)


async def get_workshop_detail(workshop_id: int) -> WorkshopDetailResponse:
    async with UnitOfWork() as uow:
        workshop = await get_approved_workshop(uow, workshop_id)
        services = await uow.workshop_services.get_by_workshop(workshop_id)
        review_count = await uow.workshop_reviews.count_by_workshop(workshop_id)
        return WorkshopDetailResponse(
            **_workshop_to_response(workshop).model_dump(),
            review_count=review_count,
            services=[_service_to_response(s) for s in services],
        )


async def search_workshops(
    q, category_id, min_price, max_price, min_rating, sort_by, page, page_size
) -> PaginatedWorkshopResponse:
    if min_price is not None and max_price is not None and min_price > max_price:
        raise AppException("min_price cannot be greater than max_price", status_code=400)

    async with UnitOfWork() as uow:
        workshops = await uow.workshops.search(
            q=q, category_id=category_id, min_price=min_price, max_price=max_price,
            min_rating=min_rating, sort_by=sort_by, limit=page_size, offset=(page - 1) * page_size,
        )
        total = await uow.workshops.count_search(q, category_id, min_price, max_price, min_rating)
        return PaginatedWorkshopResponse(
            items=[_workshop_to_response(w) for w in workshops],
            total=total, page=page, page_size=page_size,
            total_pages=_total_pages(total, page_size),
        )


async def nearby_workshops(
    lat: float, lng: float, radius_km: float, page: int, page_size: int
) -> list[WorkshopNearbyResponse]:
    async with UnitOfWork() as uow:
        rows = await uow.workshops.search_nearby(
            lat, lng, radius_km, limit=page_size, offset=(page - 1) * page_size
        )
        return [
            WorkshopNearbyResponse(**_workshop_to_response(w).model_dump(), distance_km=round(d, 2))
            for w, d in rows
        ]


async def list_workshop_services(workshop_id: int) -> list[WorkshopServiceResponse]:
    async with UnitOfWork() as uow:
        await get_approved_workshop(uow, workshop_id)
        services = await uow.workshop_services.get_by_workshop(workshop_id)
        return [_service_to_response(s) for s in services]


async def add_service(current_user: User, data: WorkshopServiceCreateRequest) -> WorkshopServiceResponse:
    workshop_id = _require_staff_workshop(current_user)

    async with UnitOfWork() as uow:
        category = await uow.service_categories.get_by_id(data.category_id)
        if category is None:
            raise AppException("Service category not found", status_code=404)

        if await uow.workshop_services.exists_for_workshop(workshop_id, data.category_id):
            raise AppException("This service is already listed for your workshop", status_code=409)

        service = WorkshopService(workshop_id=workshop_id, category_id=data.category_id, price=data.price)
        uow.workshop_services.add(service)
        try:
            await uow.commit()
        except IntegrityError:
            
            await uow.rollback()
            raise AppException("This service is already listed for your workshop", status_code=409)
        return _service_to_response(service)


def _ensure_can_manage_service(current_user: User, service: WorkshopService) -> None:
    if current_user.role == Role.ADMIN:
        return
    if current_user.role == Role.WORKSHOP_STAFF and service.workshop_id == current_user.workshop_id:
        return
    raise AppException("Not authorized to manage this service", status_code=403)


async def update_service(
    current_user: User, service_id: int, data: WorkshopServiceUpdateRequest
) -> WorkshopServiceResponse:
    async with UnitOfWork() as uow:
        service = await uow.workshop_services.get_by_id(service_id)
        if service is None:
            raise AppException("Service not found", status_code=404)
        _ensure_can_manage_service(current_user, service)

        await uow.workshop_services.update(service, {"price": data.price})
        await uow.commit()
        return _service_to_response(service)


async def remove_service(current_user: User, service_id: int) -> None:
    async with UnitOfWork() as uow:
        service = await uow.workshop_services.get_by_id(service_id)
        if service is None:
            raise AppException("Service not found", status_code=404)
        _ensure_can_manage_service(current_user, service)

        try:
            await uow.workshop_services.delete(service)
            await uow.commit()
        except IntegrityError:
            await uow.rollback()
            raise AppException(
                "This service is used by existing bookings and cannot be removed", status_code=409
            )

async def admin_list_workshops(
    current_user: User, status: str | None, q: str | None, page: int, page_size: int
) -> PaginatedWorkshopResponse:
    _require_admin(current_user)

    async with UnitOfWork() as uow:
        workshops = await uow.workshops.list_admin(status, q, page_size, (page - 1) * page_size)
        total = await uow.workshops.count_admin(status, q)
        return PaginatedWorkshopResponse(
            items=[_workshop_to_response(w) for w in workshops],
            total=total, page=page, page_size=page_size,
            total_pages=_total_pages(total, page_size),
        )


async def admin_get_workshop(current_user: User, workshop_id: int) -> WorkshopResponse:
    _require_admin(current_user)

    async with UnitOfWork() as uow:
        workshop = await uow.workshops.get_by_id(workshop_id)
        if workshop is None:
            raise AppException("Workshop not found", status_code=404)
        return _workshop_to_response(workshop)


async def admin_create_workshop(current_user: User, data: AdminWorkshopCreateRequest) -> WorkshopResponse:
    _require_admin(current_user)

    async with UnitOfWork() as uow:
        workshop = Workshop(**data.model_dump())
        uow.workshops.add(workshop)
        await uow.commit()
        return _workshop_to_response(workshop)


async def admin_update_workshop(
    current_user: User, workshop_id: int, data: AdminWorkshopUpdateRequest
) -> WorkshopResponse:
    _require_admin(current_user)

    async with UnitOfWork() as uow:
        workshop = await uow.workshops.get_by_id(workshop_id)
        if workshop is None:
            raise AppException("Workshop not found", status_code=404)

        changes = data.model_dump(exclude_unset=True)
        for required_field in ("workshop_name", "status"):  # NOT NULL columns, ignore explicit nulls
            if changes.get(required_field) is None:
                changes.pop(required_field, None)

        await uow.workshops.update(workshop, changes)
        await uow.commit()
        return _workshop_to_response(workshop)


async def admin_delete_workshop(current_user: User, workshop_id: int) -> None:
    _require_admin(current_user)

    async with UnitOfWork() as uow:
        workshop = await uow.workshops.get_by_id(workshop_id)
        if workshop is None:
            raise AppException("Workshop not found", status_code=404)

        try:
            await uow.workshops.delete(workshop)
            await uow.commit()
        except IntegrityError:
            await uow.rollback()
            raise AppException(
                "This workshop has staff, services, bookings or reviews and cannot be deleted. "
                "Set its status to 'suspended' instead.",
                status_code=409,
            )
