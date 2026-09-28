from app.utils.password import hash_password
from app.schemas.auth import RegisterRequest
from sqlalchemy.orm import Session
from app.schemas.auth import LoginRequest

from app.models.user import User
from app.schemas.user import UserResponse
from app.utils.password import verify_password
from app.utils.jwt import create_access_token
from app.common.exceptions import BussinessException
from app.schemas.auth import LoginResponse


def login(db: Session, data: LoginRequest):
    user = db.query(User).filter(User.username == data.username).first()
    #判断密码
    if not user or not verify_password(data.password, user.password):
        raise BussinessException('账号或密码错误')

    if user.status != 1:
        raise BussinessException('账号已被封禁')
    token = create_access_token(user_id=user.id)
    return LoginResponse(token=token, user=UserResponse.model_validate(user))


def register(db: Session, data: RegisterRequest):
    user = db.query(User).filter(User.username == data.username).first()
    if user:
        raise BussinessException('用户名已存在')
    user_model = User(username=data.username,
                password=hash_password(data.password),
                name=data.name or data.username,
                role="student",
                status=1)
    db.add(user_model)
    db.commit()
    db.refresh(user_model)
