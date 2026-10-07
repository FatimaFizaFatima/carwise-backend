from fastapi import APIRouter, Depends, Query, status
from app.core.dependencies import get_current_user
from app.service import chat_service
from app.schema.chat import (
    ConversationCreateRequest, ConversationResponse,
    MessageSendRequest, MessageResponse, MarkReadRequest,
)
from app.models.user_models import User

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/conversations", response_model=ConversationResponse)
async def get_or_create_conversation(
    data: ConversationCreateRequest, current_user: User = Depends(get_current_user)
):
    return await chat_service.get_or_create_conversation(current_user, data)


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(current_user: User = Depends(get_current_user)):
    return await chat_service.list_conversations(current_user)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
async def get_messages(
    conversation_id: int,
    before_id: int | None = Query(None, ge=1),
    after_id: int | None = Query(None, ge=1),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    return await chat_service.get_messages(
        current_user, conversation_id, before_id, after_id, limit
    )


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_message(
    conversation_id: int,
    data: MessageSendRequest,
    current_user: User = Depends(get_current_user),
):
    return await chat_service.send_message(current_user, conversation_id, data)


@router.post("/conversations/{conversation_id}/read")
async def mark_read(
    conversation_id: int,
    data: MarkReadRequest,
    current_user: User = Depends(get_current_user),
):
    return await chat_service.mark_read(current_user, conversation_id, data)