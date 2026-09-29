from hashlib import new
from pydantic import ConfigDict
from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    role: str
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    status: int
    model_config = ConfigDict(from_attributes=True)


class UserCraeteRequest(BaseModel):
    username: str
    password: str = '123'
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str = 'student'
    status: int = 1


class UserUpdateRequest(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    role: str | None = None
    status: int | None = None


class PasswordUpdateRequest(BaseModel):
    old_password: str
    new_password: str
