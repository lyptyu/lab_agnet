from operator import or_
from app.common.response import PageResponse
from app.common.exceptions import BussinessException
from app.schemas.lab import LabUpdateRequest, LabResponse, LabCraeteRequest
from sqlalchemy.orm import Session
from app.models.lab import Lab


def get_lab_page_list(db: Session, page: int, page_size: int,
                      keywords: str | None):
    #select * from lab where name like '%xxx%'
    query = db.query(Lab)
    if keywords:
        query = query.filter(Lab.name.ilike(f'%{keywords}%'))
    total = query.count()
    items = query.order_by(Lab.id.desc()).offset(
        (page - 1) * page_size).limit(page_size).all()
    return PageResponse(
        list=[LabResponse.model_validate(item) for item in items], total=total)


def create_lab(db: Session, data: LabCraeteRequest):
    exist = db.query(Lab).filter(Lab.name == data.name).first()
    if exist:
        raise BussinessException(message='实验室已存在')
    lab = Lab(**data.model_dump()
              )  #{'key1':'value1','key2':'value2'} -> key1=value1,key2=value2
    db.add(lab)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def update_lab(db: Session, lab_id: int, data: LabUpdateRequest):
    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BussinessException(message='实验室不存在')
    payload = data.model_dump(exclude_none=True)
    for field, value in payload.items():
        setattr(lab, field, value)
    db.commit()
    db.refresh(lab)
    return LabResponse.model_validate(lab)


def delete_lab(db: Session, lab_id: int):

    lab = db.query(Lab).filter(Lab.id == lab_id).first()
    if not lab:
        raise BussinessException(message='实验室不存在')
    db.delete(lab)
    db.commit()
