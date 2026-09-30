from datetime import datetime
from app.models.reservation import Reservation
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.common.exceptions import BussinessException
from app.models.user import User
from fastapi import Depends
from app.schemas.reservation import ReservationCreateRequest
from sqlalchemy.orm import Session


def create_reservation(db: Session, current_user: User,
                       data: ReservationCreateRequest):
    """  创建预约"""
    now = datetime.now()
    current_date = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")
    if data.date < current_date:
        raise BussinessException(message="预约日期不能小于当前日期")
    if data.end_time < data.start_time:
        raise BussinessException(message="结束时间不能小于开始时间")
    if data.date == current_date and data.start_time < current_time:
        raise BussinessException(message="预约开始时间不能小于当前时间")

    lab = db.query(Lab).filter(Lab.id == data.lab_id).first()
    if not lab:
        raise BussinessException(message="实验室不存在")
    print('labstatus', lab.status)
    if lab.status != 1:
        raise BussinessException(message="实验室未开放预约")
    if lab.open_time and data.start_time < lab.open_time:
        raise BussinessException(message="预约时间不能早于实验室开放时间")
    if lab.open_time and data.end_time > lab.close_time:
        raise BussinessException(message="预约时间不能晚于实验室结束时间")
    # quipment_id不为空 说明这次预约的是设备
    if data.equipment_id:
        equipment = db.query(Equipment).filter(
            Equipment.id == data.equipment_id).first()
    if not equipment:
        raise BussinessException('实验室设备不存在')
    if equipment.status != 1:
        raise BussinessException('实验室设备正在维修')
    # 实验室设备是否可预约
    query = db.query(Reservation).filter(
        Reservation.lab_id == data.lab_id, Reservation.date == data.date,
        Reservation.status.in_([0, 1]), Reservation.start_time < data.end_time,
        Reservation.end_time > data.start_time)
    if data.equipment_id:  #预约设备
        query.filter(Reservation.equipment_id == data.equipment_id)
    else:  #预约实验室
        query.filter(Reservation.equipment_id.is_(None))
    if query.first():
        raise BussinessException(message='实验室设备该时段已经预约')

    reservation_model = Reservation(user_id=current_user.id,
                                    lab_id=data.lab_id,
                                    equipment_id=data.equipment_id,
                                    date=data.date,
                                    start_time=data.start_time,
                                    end_time=data.end_time,
                                    remark=data.remark,
                                    status=0)
    db.add(reservation_model)
    db.commit()
