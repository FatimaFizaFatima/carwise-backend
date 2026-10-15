from pydantic import BaseModel, ConfigDict, Field


class ServiceCategoryCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(min_length=1, max_length=100)
    icon: str | None = Field(default=None, max_length=255)


class ServiceCategoryUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str | None = Field(default=None, min_length=1, max_length=100)
    icon: str | None = Field(default=None, max_length=255)


class ServiceCategoryResponse(BaseModel):
    id: int
    name: str
    icon: str | None = None
