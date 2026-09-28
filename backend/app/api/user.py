from app.dependencies.auth import get_current_user
from app.models.user import User

from fastapi import APIRouter, Depends
from app.schemas.user import UserResponse
from app.common.response import Response
router = APIRouter(prefix="/user", tags=['用户信息'])

@router.get('/info')
def get_user_info(current_user: User = Depends(get_current_user)):
    return Response.success(data=UserResponse.model_validate(current_user))
