from app.models.lab import Lab
from operator import or_
from app.common.response import PageResponse
from app.common.exceptions import BussinessException
from app.schemas.equipment import EquipmentCreateRequest, EquipmentResponse, EquipmentUpdateRequest
from sqlalchemy.orm import Session
from app.models.equipment import Equipment


def get_equipment_page_list(db: Session,
                            page: int,
                            page_size: int,
                            keywords: str | None,
                            lab_id: int | None = None):
    #select * from equipment where name like '%xxx%'
    query = db.query(Equipment)
    if lab_id:
        query = query.filter(Equipment.lab_id == lab_id)
    if keywords:
        query = query.filter(Equipment.name.ilike(f'%{keywords}%'))
    total = query.count()
    items = query.order_by(Equipment.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    result = []
    for item in items:
        res = EquipmentResponse.model_validate(item)
        res.lab_name = item.lab.name if item.lab else None
        result.append(res)
    return PageResponse(list=result, total=total)


def create_equipment(db: Session, data: EquipmentCreateRequest):
    exist = db.query(Equipment).filter(Equipment.name == data.name).first()
    if exist:
        raise BussinessException(message='实验室设备已存在')
    equipment = Equipment(**data.model_dump(
    ))  #{'key1':'value1','key2':'value2'} -> key1=value1,key2=value2
    db.add(equipment)
    db.commit()
    db.refresh(equipment)
    res = EquipmentResponse.model_validate(equipment)
    res.lab_name = equipment.lab.name if equipment.lab else None
    return res


def update_equipment(db: Session, equipment_id: int,
                     data: EquipmentUpdateRequest):
    equipment = db.query(Equipment).filter(
        Equipment.id == equipment_id).first()
    if not equipment:
        raise BussinessException(message='实验室设备不存在')

    payload = data.model_dump(exclude_none=True)
    lab_id = payload.get('lab_id', equipment.lab_id)
    name = payload.get('name', equipment.name)
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BussinessException(message='实验室不存在')
    exist = db.query(Equipment).filter(Equipment.lab_id == lab_id,
                                       Equipment.name == name,Equipment.id != equipment_id)
    
    if exist:
        raise BussinessException(message='同一个实验室不能存在同名设备')
    for field, value in payload.items():
        setattr(equipment, field, value)
    db.commit()
    db.refresh(equipment)
    res = EquipmentResponse.model_validate(equipment)
    res.lab_name = equipment.lab.name if equipment.lab else None
    return res


def delete_equipment(db: Session, equipment_id: int):

    equipment = db.query(Equipment).filter(
        Equipment.id == equipment_id).first()
    if not equipment:
        raise BussinessException(message='实验室设备不存在')
    db.delete(equipment)
    db.commit()
