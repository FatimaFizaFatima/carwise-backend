from datetime import datetime
from pydantic import BaseModel, field_validator


class ConversationCreateRequest(BaseModel):
    booking_id: int


class MessageSendRequest(BaseModel):
    text: str

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty")
        if len(value) > 2000:
            raise ValueError("Message cannot be longer than 2000 characters")
        return value


class MarkReadRequest(BaseModel):
    up_to_message_id: int


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    sender_id: int
    text: str
    status: str
    delivered_at: datetime | None = None
    read_at: datetime | None = None
    created_at: datetime


class ConversationResponse(BaseModel):
    id: int
    booking_id: int
    booking_reference: str
    other_party_name: str
    last_message: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0

class MarkDeliveredRequest(BaseModel):
    up_to_message_id: int

