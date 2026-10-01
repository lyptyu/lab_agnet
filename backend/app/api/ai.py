from app.schemas.ai import ChatMessage
from app.common.response import Response
from app.services import ai_service
from app.database import get_db
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from fastapi import Depends
from app.models.user import User
from app.schemas.ai import ChatRequest
from fastapi import APIRouter

router = APIRouter(prefix="/ai", tags=["大模型ai相关api"])


@router.post("/chat")
def chat(data: ChatRequest,
         current_user: User = Depends(get_current_user),
         ):
    content = ai_service.chat(data)
    return Response.success(data=ChatMessage(role='assistant', content=content).model_dump())
