from app.config import settings
from datetime import datetime, timedelta
import jwt


def create_access_token(user_id: int) -> str:
    """创建jwt"""
    expire = datetime.now() + timedelta(
        hours=settings.JWT_EXPIRE_HOURS)
    payload = {"user_id": user_id, "exp": expire}
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm = settings.JWT_ALGORITHM
    )

def decode_access_token(token:str)->dict:
    """解码jwt"""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms = [settings.JWT_ALGORITHM]
    )