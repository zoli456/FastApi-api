from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete, update
from db import database
from models import users, roles, user_roles, messages
from utils import hash_password, get_current_user
from pydantic import BaseModel, EmailStr

router = APIRouter()

# Admin Password Reset Schema
class AdminPasswordResetRequest(BaseModel):
    user_id: int
    new_password: str

# Admin Delete User Schema
class AdminDeleteUserRequest(BaseModel):
    user_id: int

class AdminUpdateEmailRequest(BaseModel):
    user_id: int
    new_email: EmailStr

class AdminDeleteMessageRequest(BaseModel):
    message_id: int


# 🔐 Helper Function: Check if User is Admin
async def is_admin(user):
    query = select(roles.c.name).select_from(
        user_roles.join(roles, user_roles.c.role_id == roles.c.id)
    ).where(user_roles.c.user_id == user["id"])

    user_roles_list = await database.fetch_all(query)
    roles_list = [role["name"] for role in user_roles_list]

    if "admin" not in roles_list:
        raise HTTPException(status_code=403, detail="Admin access required")


# 🔹 Admin: Change Any User’s Password
@router.put("/change-password")
async def admin_change_password(
        request: AdminPasswordResetRequest, current_user: dict = Depends(get_current_user)
):
    await is_admin(current_user)  # Ensure admin access

    # Hash new password and update in DB
    new_password_hash = hash_password(request.new_password)
    query = (
        update(users)
        .where(users.c.id == request.user_id)
        .values(password_hash=new_password_hash)
    )
    await database.execute(query)

    return {"message": "Password changed successfully"}


# 🔹 Admin: Delete Any User
@router.delete("/delete-user")
async def admin_delete_user(
        request: AdminDeleteUserRequest, current_user: dict = Depends(get_current_user)
):
    await is_admin(current_user)  # Ensure admin access

    # Delete user from database
    query = delete(users).where(users.c.id == request.user_id)
    await database.execute(query)

    return {"message": "User deleted successfully"}

@router.put("/change-email")
async def admin_change_email(
        request: AdminUpdateEmailRequest, current_user: dict = Depends(get_current_user)
):
    await is_admin(current_user)  # Ensure admin access

    # Check if the new email is already in use
    existing_email_query = select(users.c.id).where(users.c.email == request.new_email)
    existing_user = await database.fetch_one(existing_email_query)

    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already in use")

    # Update email in database
    query = (
        update(users)
        .where(users.c.id == request.user_id)
        .values(email=request.new_email)
    )
    await database.execute(query)

    return {"message": "Email address updated successfully"}

@router.delete("/admin/messages")
async def admin_delete_message(
        request: AdminDeleteMessageRequest, current_user: dict = Depends(get_current_user)
):
    await is_admin(current_user)  # Ensure admin access

    # Check if message exists
    query = select(messages).where(messages.c.id == request.message_id)
    message = await database.fetch_one(query)

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Delete the message
    delete_query = delete(messages).where(messages.c.id == request.message_id)
    await database.execute(delete_query)

    return {"message": "Message deleted successfully"}