from app.unit_of_work.unit_of_work import UnitOfWork
from app.core.exceptions import AppException
from app.core.securtiy import hash_password
from app.core.roles import Role, AccountStatus, WorkshopStatus
from app.models.user_models import User
from app.models.workshop import Workshop
from app.schema.workshop import WorkshopStaffRegisterRequest, WorkshopStaffRegisterResponse
from app.schema.auth import MessageResponse


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