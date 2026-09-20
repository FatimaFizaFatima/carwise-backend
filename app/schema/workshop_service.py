from pydantic import BaseModel


class WorkshopServiceCreateRequest(BaseModel):

    category_id : int
    price : float



class WorkshopServiceResponse(BaseModel):

    id : int
    workshop_id : int
    category_id : int
    price : float

