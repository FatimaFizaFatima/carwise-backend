from pydantic import BaseModel, Field


class WorkshopServiceCreateRequest(BaseModel):
    category_id: int = Field(gt=0)
    price: float = Field(gt=0, le=1_000_000)


class WorkshopServiceUpdateRequest(BaseModel):
    price: float = Field(gt=0, le=1_000_000)


class WorkshopServiceResponse(BaseModel):
    id: int
    workshop_id: int
    category_id: int
    price: float
