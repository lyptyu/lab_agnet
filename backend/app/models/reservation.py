from app.models.equipment import Equipment
from app.models.lab import Lab
from sqlalchemy.orm import relationship
from app.models.user import User
from fastapi import status
from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Reservation(Base):
    __tablename__ = 'reservations'
    __table_args__ = {'comment': '预约信息表'}
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'),
                                         comment="用户ID",
                                         nullable=False)
    lab_id: Mapped[int] = mapped_column(ForeignKey('labs.id'),
                                        comment="实验室ID",
                                        nullable=False)
    equipment_id: Mapped[int] = mapped_column(ForeignKey('equipments.id'),
                                              comment="设备ID,空表示预约实验室",
                                              nullable=True)
    date: Mapped[str] = mapped_column(String(20),
                                      comment="预约日期",
                                      nullable=False)
    start_time: Mapped[str] = mapped_column(String(20),
                                            comment="开始时间",
                                            nullable=False)
    end_time: Mapped[str] = mapped_column(String(20),
                                          comment="结束时间",
                                          nullable=False)
    remark: Mapped[str] = mapped_column(String(255),
                                        comment="备注",
                                        nullable=True)
    status: Mapped[int] = mapped_column(comment="预约状态 0待审核 1已通过 2已拒绝 3已取消",
                                        nullable=False)

    user: Mapped[User] = relationship()
    lab: Mapped[Lab] = relationship()
    equipment: Mapped[Equipment] = relationship()
