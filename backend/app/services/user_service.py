from app.schemas.user import UserUpdateRequest
from sqlalchemy.orm import Session
from app.schemas.user import UserResponse
from app.models.user import User
def get_user_info(user:User) -> UserResponse:
    return UserResponse.model_validate(user)

def update_user_info(db: Session, user: User, data: UserUpdateRequest):
    user_dict = data.model_dump(exclude_none=True)
    for field,value in user_dict.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)