import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from db import database
from models import users, user_roles, roles
from utils import verify_password, hash_password, get_current_user
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

class UpdateEmailRequest(BaseModel):
    new_email: str

class UpdatePasswordRequest(BaseModel):
    old_password: str
    new_password: str



@router.put("/update-email", dependencies=[Depends(get_current_user)])
async def update_email(data: UpdateEmailRequest, user=Depends(get_current_user)):
    # Check if the new email is already in use
    query = users.select().where(users.c.email == data.new_email)
    existing_user = await database.fetch_one(query)

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Update email
    query = users.update().where(users.c.id == user["id"]).values(email=data.new_email)
    await database.execute(query)

    return {"message": "Email updated successfully"}

@router.put("/update-password", dependencies=[Depends(get_current_user)])
async def update_password(data: UpdatePasswordRequest, user=Depends(get_current_user)):
    # Verify old password
    if not verify_password(data.old_password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Incorrect old password")

    # Hash new password and update it
    new_hashed_password = hash_password(data.new_password)
    query = users.update().where(users.c.id == user["id"]).values(password_hash=new_hashed_password)
    await database.execute(query)

    return {"message": "Password updated successfully"}

@router.get("/me", dependencies=[Depends(get_current_user)])
async def read_users_me(user=Depends(get_current_user)):
    # Fetch User Roles
    role_query = user_roles.join(roles, user_roles.c.role_id == roles.c.id)
    query = role_query.select().where(user_roles.c.user_id == user["id"])
    user_roles_list = await database.fetch_all(query)

    roles_list = [{"id": r["id"], "name": r["name"]} for r in user_roles_list]

    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "roles": roles_list
    }
