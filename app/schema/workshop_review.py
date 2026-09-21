from datetime import datetime
from pydantic import BaseModel, field_validator


class ReviewCreateRequest(BaseModel):
    booking_id: int
    rating: int
    comment: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: int) -> int:
        if not (1 <= value <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return value


class ReviewResponse(BaseModel):
    id: int
    workshop_id: int
    user_id: int
    booking_id: int
    rating: int
    comment: str | None
    created_at: datetime