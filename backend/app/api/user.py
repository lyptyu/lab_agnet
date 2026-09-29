from app.schemas.user import UserCreateRequest
from app.dependencies.auth import get_current_admin
from app.schemas.user import PasswordUpdateRequest
from sqlalchemy.orm import Session
from app.schemas.user import UserUpdateRequest
from app.dependencies.auth import get_current_user
from app.models.user import User

from fastapi import APIRouter, Depends
from app.schemas.user import UserResponse
from app.common.response import Response

from app.services import user_service
from app.database import get_db

router = APIRouter(prefix="/user", tags=['用户信息'])


@router.get('/me')
def get_user_info(current_user: User = Depends(get_current_user)):
    return Response.success(data=user_service.get_user_info(current_user))


@router.put('/me')
def update_user_info(data: UserUpdateRequest,
                     current_user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    res = user_service.update_user_info(db, current_user, data)
    return Response.success(data=res)


@router.put('/password')
def update_password(data: PasswordUpdateRequest,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    res = user_service.update_password(db, current_user, data)
    return Response.success()


@router.get('/list')
def get_user_list(page: int = 1,
                  page_size: int = 10,
                  keywords: str | None = None,
                  current_user: User = Depends(get_current_admin),
                  db: Session = Depends(get_db)):
    res = user_service.get_user_page_list(db, page, page_size, keywords)
    return Response.success(data=res)


@router.post('')
def create_user(data: UserCreateRequest,
                current_user: User = Depends(get_current_admin),
                db: Session = Depends(get_db)):
    res = user_service.create_user(db, data)
    return Response.success(data=res)


@router.put('/{user_id}')
def update_user(user_id: int,
                data: UserUpdateRequest,
                current_user: User = Depends(get_current_admin),
                db: Session = Depends(get_db)):
    res = user_service.update_user(db, user_id, data)
    return Response.success(data=res)
@router.delete('/{user_id}')
def delete_user(user_id: int,
                current_user: User = Depends(get_current_admin),
                db: Session = Depends(get_db)):
    user_service.delete_user(db, user_id, current_user)
    return Response.success()
