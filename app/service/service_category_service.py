from app.models.service_category import ServiceCategoryModel
from app.unit_of_work.unit_of_work import UnitOfWork
from app.schema.service_category import (
    ServiceCategoryCreateRequest,
    ServiceCategoryResponse,
    ServiceCategoryUpdateRequest,
)
from app.core.roles import Role
from app.models.user_models import User
from app.core.exceptions import AppException
from sqlalchemy.exc import IntegrityError


def _to_response(c: ServiceCategoryModel) -> ServiceCategoryResponse:
    return ServiceCategoryResponse(id=c.id, name=c.name, icon=c.icon)


def _require_admin(current_user: User, action: str) -> None:
    if current_user.role != Role.ADMIN:
        raise AppException(f"Only admin can {action} service categories", status_code=403)


async def list_categories() -> list[ServiceCategoryResponse]:
    async with UnitOfWork() as uow:
        categories = await uow.service_categories.get_all()
        return [_to_response(c) for c in categories]


async def get_category(category_id: int) -> ServiceCategoryResponse:
    async with UnitOfWork() as uow:
        category = await uow.service_categories.get_by_id(category_id)
        if category is None:
            raise AppException("Category not found", status_code=404)
        return _to_response(category)


async def create_category(current_user: User, data: ServiceCategoryCreateRequest) -> ServiceCategoryResponse:
    _require_admin(current_user, "create")

    async with UnitOfWork() as uow:
        if await uow.service_categories.get_by_name(data.name) is not None:
            raise AppException("Category already exist", status_code=409)

        category = ServiceCategoryModel(name=data.name, icon=data.icon)
        uow.service_categories.add(category)
        try:
            await uow.commit()
        except IntegrityError:
            await uow.rollback()
            raise AppException("Category already exist", status_code=409)
        return _to_response(category)


async def update_category(
    current_user: User, category_id: int, data: ServiceCategoryUpdateRequest
) -> ServiceCategoryResponse:
    _require_admin(current_user, "update")

    async with UnitOfWork() as uow:
        category = await uow.service_categories.get_by_id(category_id)
        if category is None:
            raise AppException("Category not found", status_code=404)

        changes = data.model_dump(exclude_unset=True)
        if changes.get("name") is None:
            changes.pop("name", None)  # name is NOT NULL, ignore an explicit null

        new_name = changes.get("name")
        if new_name is not None and await uow.service_categories.get_by_name(new_name, exclude_id=category_id):
            raise AppException("Category already exist", status_code=409)

        await uow.service_categories.update(category, changes)
        try:
            await uow.commit()
        except IntegrityError:
            await uow.rollback()
            raise AppException("Category already exist", status_code=409)
        return _to_response(category)


async def delete_category(current_user: User, category_id: int) -> None:
    _require_admin(current_user, "delete")

    async with UnitOfWork() as uow:
        category = await uow.service_categories.get_by_id(category_id)
        if category is None:
            raise AppException("Category not found", status_code=404)

        if await uow.workshop_services.exists_for_category(category_id):
            raise AppException(
                "This category is used by workshop services and cannot be deleted", status_code=409
            )

        try:
            await uow.service_categories.delete(category)
            await uow.commit()
        except IntegrityError:
            await uow.rollback()
            raise AppException(
                "This category is in use and cannot be deleted", status_code=409
            )
