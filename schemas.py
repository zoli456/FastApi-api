from typing import List

from pydantic import BaseModel, EmailStr, Field


class UserUpdateEmail(BaseModel):
    new_email: EmailStr = Field(..., min_length=5, max_length=100)

class UserUpdatePassword(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=100)
    new_password: str = Field(..., min_length=6, max_length=100)

class Role(BaseModel):
    id: int
    name: str

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    roles: List[Role]

class Token(BaseModel):
    access_token: str
    token_type: str
