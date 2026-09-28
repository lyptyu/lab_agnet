
from app.schemas.user import UserResponse
from pydantic import BaseModel
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: UserResponse

class RegisterRequest(BaseModel):
    username: str
    password: str
    name: str | None = None
