from pydantic import BaseModel, Field
from typing import Optional


class LoginIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class TokenOut(BaseModel):
    token: str
    user: dict
    message: str = "Login successful"


class LogoutIn(BaseModel):
    token: str


class UserCreateIn(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=128)
    is_admin: bool = False
    is_active: bool = True


class UserUpdateIn(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=128)
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None
    new_password: Optional[str] = Field(default=None, min_length=8, max_length=128)


class MsgOut(BaseModel):
    message: str
    details: Optional[str] = None
