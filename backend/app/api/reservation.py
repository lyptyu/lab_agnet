from app.common.response import Response
from app.services import reservation_service
from app.database import get_db
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from fastapi import Depends
from app.models.user import User
from app.schemas.reservation import ReservationCreateRequest
from fastapi import APIRouter

router = APIRouter(prefix="/reservation", tags=['预约相关api'])


@router.post('')
def create_reservation(data: ReservationCreateRequest,
                       current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    reservation_service.create_reservation(db, current_user, data)
    return Response.success()
