from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update, delete
from db import database
from models import messages, users
from utils import get_current_user
from pydantic import BaseModel, Field

router = APIRouter()

class MessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=4, max_length=1024)

class MessageUpdateRequest(BaseModel):
    message_id: int
    new_content: str = Field(..., min_length=4, max_length=1024)


class MessageDeleteRequest(BaseModel):
    message_id: int

class MessageResponse(BaseModel):
    id: int
    user_id: int
    username: str
    content: str
    created_at: str
    updated_at: str

    @classmethod
    def from_record(cls, record):
        """Convert database result into Pydantic model"""
        return cls(
            id=record["id"],
            user_id=record["user_id"],
            username=record["username"],
            content=record["content"],
            created_at=record["created_at"].isoformat(),
            updated_at=record["updated_at"].isoformat(),
        )
@router.post("/post")
async def create_message(
        request: MessageCreateRequest, current_user: dict = Depends(get_current_user)
):
    query = messages.insert().values(user_id=current_user["id"], content=request.content)
    message_id = await database.execute(query)
    return {"message": "Message created successfully", "message_id": message_id}


@router.put("/update")
async def update_message(
        request: MessageUpdateRequest, current_user: dict = Depends(get_current_user)
):
    # Check if message exists and belongs to the current user
    query = select(messages).where(messages.c.id == request.message_id)
    message = await database.fetch_one(query)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only edit your own messages")

    # Update message content
    update_query = (
        update(messages)
        .where(messages.c.id == request.message_id)
        .values(content=request.new_content)
    )
    await database.execute(update_query)
    return {"message": "Message updated successfully"}


@router.delete("/delete")
async def delete_message(
        request: MessageDeleteRequest, current_user: dict = Depends(get_current_user)
):
    # Check if message exists and belongs to the current user
    query = select(messages).where(messages.c.id == request.message_id)
    message = await database.fetch_one(query)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message["user_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only delete your own messages")

    # Delete the message
    delete_query = delete(messages).where(messages.c.id == request.message_id)
    await database.execute(delete_query)
    return {"message": "Message deleted successfully"}

@router.get("/all", response_model=List[MessageResponse])
async def get_all_messages(current_user: dict = Depends(get_current_user)):
    query = select(
        messages.c.id,
        messages.c.user_id,
        users.c.username,
        messages.c.content,
        messages.c.created_at,
        messages.c.updated_at,
    ).join(users, messages.c.user_id == users.c.id)

    all_messages = await database.fetch_all(query)

    return [MessageResponse.from_record(msg) for msg in all_messages]