from typing import Optional
from pydantic import BaseModel, EmailStr

class UserRole(BaseModel):
    name: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserResponse(BaseModel):
    username: str
    role: UserRole

