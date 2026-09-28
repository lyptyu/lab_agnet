from app.services import auth_service
from app.common.response import Response
from fastapi import APIRouter, Depends
from app.schemas.auth import LoginRequest, RegisterRequest
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/auth", tags=['权限验证'])


@router.post('/login')
def login(data: LoginRequest, db: Session = Depends(get_db)):
    result = auth_service.login(db, data)
    return Response.success(message='登陆成功', data=result)


@router.post('/register')
def login(data: RegisterRequest, db: Session = Depends(get_db)):
    auth_service.register(db, data)
    return Response.success(message='注册成功')
