from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReviewCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    booking_id: int = Field(gt=0)
    rating: int
    comment: str | None = Field(default=None, max_length=1000)

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
    reviewer_name: str
    reviewer_avatar_url: str | None = None
