from app.schemas.user import UserCraeteRequest
from operator import or_
from app.common.response import PageResponse
from app.schemas.user import PasswordUpdateRequest
from app.utils.password import hash_password
from app.common.exceptions import BussinessException
from app.utils.password import verify_password
from app.schemas.user import UserUpdateRequest
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse
from app.models.user import User


def get_user_info(user: User) -> UserResponse:
    return UserResponse.model_validate(user)


def update_user_info(db: Session, user: User, data: UserUpdateRequest):
    user_dict = data.model_dump(exclude_none=True)
    for field, value in user_dict.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def update_password(db: Session, user: User, data: PasswordUpdateRequest):

    if not verify_password(data.old_password, user.password):
        raise BussinessException(message='旧密码不正确')
    if data.old_password == data.new_password:
        raise BussinessException(message='新密码不能和原密码相同')
    user.password = hash_password(data.new_password)
    db.commit()
    db.refresh(user)


def get_user_page_list(db: Session, page: int, page_size: int,
                       keywords: str | None):
    #select * from user where username like '%张%' or name like '%张%'
    query = db.query(User)
    if keywords:
        query = query.filter(
            or_(User.username.ilike(f'%{keywords}%'),
                User.name.ilike(f'%{keywords}%')))
    total = query.count()
    items = query.order_by(User.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return PageResponse(
        list=[UserResponse.model_validate(item) for item in items],
        total=total)


def create_user(db: Session, data: UserCraeteRequest):
    exist = db.query(User).filter(User.username == data.username).first()
    if exist:
        raise BussinessException(message='账号已存在')
    user = User(username=data.username,
                password=hash_password(data.password),
                name=data.name,
                role=data.role,
                email=data.email,
                phone=data.phone,
                avatar=data.avatar,
                status=data.status)
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def update_user(db: Session, user_id: int, data: UserUpdateRequest):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BussinessException(message='用户不存在')
    payload = data.model_dump(exclude_none=True)
    for field, value in payload.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


def delete_user(db: Session, user_id: int, current_user=User):
    if user_id == current_user.id:
        raise BussinessException(message='不能删除自己')
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise BussinessException(message='用户不存在')
    db.delete(user)
    db.commit()