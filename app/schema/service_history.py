from datetime import datetime, date
from pydantic import BaseModel, field_validator

class AddExpenseRequest(BaseModel):

    car_id : int
    title : str
    cost : float
    service_details : str | None = None
    workshop_name : str | None = None
    service_date : date

    @field_validator("cost")
    @classmethod
    def validate_cost(cls, value : float) -> float:
        if value <= 0:
            raise ValueError("Cost must be greater than zero")
        
        return value
    @field_validator("service_date")
    @classmethod
    def validate_service(cls, value : date) -> date:
        if value > date.today():
            raise ValueError("Service date cannot be in the future")
        return value

class ServiceHistoryResponse(BaseModel):

    id : int
    car_id : int
    booking_id : int | None
    title : str
    cost : float
    service_details : str | None = None
    workshop_name : str | None = None
    attachment_url : str | None = None
    service_date : date
    status : str = "completed"
    created_at : datetime
    is_manual : bool

    