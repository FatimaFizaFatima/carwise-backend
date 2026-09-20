from pydantic import BaseModel


class ServiceCategoryCreateRequest(BaseModel):

    name : str
    icon : str | None = None

class ServiceCategoryResponse(BaseModel):

    id : int
    name : str
    icon : str | None = None

