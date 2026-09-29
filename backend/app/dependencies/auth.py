from app.common.exceptions import BussinessException
from app.models.user import User
from fastapi import status
from fastapi import HTTPException
from app.utils.jwt import decode_access_token
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme),
                     db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="登录状态失效，请重新登录")
    user_id = payload.get('user_id')
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="无效的登录凭证")
    #查询用户信息
    user = db.query(User).filter(User.id == user_id).first()
    if user.status != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="用户被封禁")
    return user


def get_current_admin(current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)) -> User:
    if current_user.role != 'admin':
        raise BussinessException(message='无权限访问', code=403)
    return current_user
