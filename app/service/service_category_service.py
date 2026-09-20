from app.models.service_category import ServiceCategoryModel
from app.unit_of_work.unit_of_work import UnitOfWork
from app.schema.service_category import ServiceCategoryCreateRequest, ServiceCategoryResponse
from app.core.roles import Role
from app.models.user_models import User
from app.core.exceptions import AppException

def _to_response(c : ServiceCategoryModel) -> ServiceCategoryResponse:
    return ServiceCategoryResponse(id = c.id, name = c.name, icon = c.icon)

async def list_categories() -> list[ServiceCategoryResponse]:
    async with UnitOfWork() as uow:
        categories = await uow.service_categories.get_all()
        return [_to_response(c) for c in categories]

async def create_category(current_user : User, data : ServiceCategoryCreateRequest) -> ServiceCategoryResponse:
    if current_user.role != Role.ADMIN:
        raise AppException("Only admin can create service categories", status_code=403)

    async with UnitOfWork() as uow:
        if await uow.service_categories.get_by_name(data.name) is not None:
            raise AppException("Category already exist", status_code=409)

        category = ServiceCategoryModel(name = data.name, icon = data.icon)
        uow.service_categories.add(category)
        await uow.commit()
        return _to_response(category)

async def delete_category(current_user : User, category_id : int) -> None:

    if current_user.role != Role.ADMIN:
        raise AppException("Only admin can delete the service category", status_code=403)

    async with UnitOfWork() as uow:
        category = await uow.service_categories.get_by_id(category_id)
        if category is None:
            raise AppException("Category not found", status_code=404)
        await uow.service_categories.delete(category)
        await uow.commit()


    