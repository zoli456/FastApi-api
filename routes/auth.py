import os
import re
from datetime import timedelta
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, constr, validator
from db import database
from models import users, roles, user_roles
from utils import hash_password, verify_password, create_access_token

router = APIRouter()

# Strong password validation function
def validate_password(password: str):
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must contain at least one uppercase letter.")
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must contain at least one lowercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must contain at least one digit.")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise ValueError("Password must contain at least one special character.")
    return password

# Request schemas with validation
class RegisterRequest(BaseModel):
    username: constr(min_length=3, max_length=50)
    email: EmailStr
    password: constr(min_length=8)

    # Custom password validation
    @validator("password")
    def password_strength(cls, value):
        return validate_password(value)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

@router.post("/register")
async def register(user: RegisterRequest):
    # Check if email already exists
    query = users.select().where(users.c.email == user.email)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash password and store user
    hashed_password = hash_password(user.password)
    query = users.insert().values(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    user_id = await database.execute(query)

    # Assign default "user" role
    query = roles.select().where(roles.c.name == "user")
    user_role = await database.fetch_one(query)
    if user_role:
        await database.execute(user_roles.insert().values(user_id=user_id, role_id=user_role["id"]))

    return {"message": "User registered successfully"}

@router.post("/login", response_model=TokenResponse)
async def login(request: Request, login_data: LoginRequest):
    body = await request.json()

    # Check if user exists
    query = users.select().where(users.c.email == login_data.email)
    user = await database.fetch_one(query)
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Fetch user roles
    role_query = user_roles.join(roles, user_roles.c.role_id == roles.c.id)
    query = role_query.select().where(user_roles.c.user_id == user["id"])
    user_roles_list = await database.fetch_all(query)
    roles_list = [r["name"] for r in user_roles_list]

    # Generate JWT token
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)))
    access_token = create_access_token(
        data={"sub": user["email"], "roles": roles_list},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}