import asyncio
from app.database import SessionLocal
from app.common.response import PageResponse
from app.schemas.reservation import ReservationResponse
from datetime import datetime
from app.models.reservation import Reservation
from app.models.equipment import Equipment
from app.models.lab import Lab
from app.common.exceptions import BussinessException
from app.models.user import User
from fastapi import Depends
from app.schemas.reservation import ReservationCreateRequest
from sqlalchemy.orm import Session


def ger_reservation_page_list(db: Session,
                              current_user: User,
                              page: int,
                              page_size: int,
                              status: int | None = None):
    """获取预约记录"""
    query = db.query(Reservation)
    if current_user.role != 'admin':
        query = query.filter(Reservation.user_id == current_user.id)
    if status is not None:
        query = query.filter(Reservation.status == status)
    total = query.count()
    items = query.order_by(Reservation.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    print('items', items)
    result = []
    for item in items:
        res = ReservationResponse.model_validate(item)
        res.user_name = item.user.name if item.user else None
        res.lab_name = item.lab.name if item.lab else None
        res.equipment_name = item.equipment.name if item.equipment else None
        res.type = "设备" if item.equipment_id else "实验室"
        result.append(res)
    return PageResponse(total=total, list=result)


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
    print('data.equipment_id', data.equipment_id)
    if data.equipment_id:  #预约设备
        query = query.filter(Reservation.equipment_id == data.equipment_id)
    else:  #预约实验室
        query = query.filter(Reservation.equipment_id.is_(None))
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
    db.refresh(reservation_model)
    print(f'[reservation] 新建预约成功 id={reservation_model.id} '
          f'user_id={current_user.id} lab_id={data.lab_id} '
          f'equipment_id={data.equipment_id} '
          f'{data.date} {data.start_time}~{data.end_time}')


def cancel_reservation(db: Session, current_user: User, reservation_id: int):
    item = db.query(Reservation).filter(
        Reservation.id == reservation_id).first()
    if not item:
        raise BussinessException(message="预约记录不存在")
    if item.user_id != current_user.id:
        raise BussinessException(message="无权限操作", code=403)
    if item.status != 0:
        raise BussinessException(message="预约记录已审核，无法取消")
    item.status = 3
    db.commit()


def audit_reservation(db: Session, reservation_id: int, status: int):
    if status not in [1, 2]:
        raise BussinessException(message='审核状态错误')
    item = db.query(Reservation).filter(
        Reservation.id == reservation_id).first()
    if not item:
        raise BussinessException(message="预约记录不存在")
    if item.status != 0:
        raise BussinessException(message="预约记录已审核，无法审核")
    item.status = status
    db.commit()


def expire_pending_reservations():
    db = SessionLocal()
    try:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        items = db.query(Reservation).filter(
            Reservation.status == 0).all()  #拿到所有待审核预约单
        changed = False
        for item in items:
            if item.date < today or (item.date == today
                                     and item.end_time <= time):
                item.status = 3  # 过期自动驳回
                changed = True
        if changed:
            db.commit()
    finally:
        db.close()


async def run_exire_scan():
    """1分钟扫描一次"""
    while True:
        print('run_exire_scan正在执行中')
        expire_pending_reservations()
        await asyncio.sleep(60)

