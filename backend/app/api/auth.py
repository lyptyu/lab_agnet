from app.schemas.auth import LoginResponse
from app.common.exceptions import BussinessException
from app.common.response import Response
from app.models.user import User
from app.schemas.user import UserResponse
from fastapi import APIRouter, Depends
from app.schemas.auth import LoginRequest

from sqlalchemy.orm import Session
from app.database import get_db
from app.utils.password import verify_password
from app.utils.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=['权限验证'])


@router.post('/login')
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()
    #判断密码
    if not user or not verify_password(data.password, user.password):
        raise BussinessException('账号或密码错误')

    if user.status != 1:
        raise BussinessException('账号已被封禁')
    token = create_access_token(user_id=user.id)
    # return Response.success(data={
    #     "token": token,
    #     "user": UserResponse.model_validate(user)
    # })
    return Response.success(message='登陆成功',
                            data = LoginResponse(
                                token=token,
                                user=UserResponse.model_validate(user)))
