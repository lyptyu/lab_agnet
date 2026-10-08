from datetime import datetime
from app.common.exceptions import BussinessException
from app.services import reservation_service
from app.models.reservation import Reservation
from app.services import equipment_service
from app.services import lab_service
import json
import traceback
from app.services import kb_service
from app.models.user import User
from langchain_core.tools import tool
from sqlalchemy.orm import Session


def build_tools(db: Session, current_user: User):

    @tool(description="根据用户提问检索知识库")
    def search_lab_docs(query: str) -> str:
        try:
            kb_service.search(query) or "没有检索到相关资料"
        except Exception as exc:
            return json.dumps({
                "ok": False,
                "error": str(exc)
            },
                              ensure_ascii=False)

    @tool(description="查询开发的实验室列表")
    def list_open_labs(keywords: str = "") -> str:
        try:
            keywords = keywords.strip() or None
            page = lab_service.get_lab_page_list(db,
                                                 page=1,
                                                 page_size=10,
                                                 keywords=keywords,
                                                 status=1)
            rows = [{
                "id": item.id,
                "name": item.name,
                "location": item.location,
                "capacity": item.capacity,
                "open_time": item.open_time,
                "close_time": item.close_time,
            } for item in page.list]
            return json.dumps({
                "total": page.total,
                "labs": rows
            },
                              ensure_ascii=False)
        except Exception as exc:
            return json.dumps({
                "ok": False,
                "error": str(exc)
            },
                              ensure_ascii=False)

    @tool(description="查询某个实验室设备列表")
    def list_lab_equipments(lab_id: int, keywords: str = "") -> str:
        try:
            keywords = keywords.strip() or None
            page = equipment_service.get_equipment_page_list(
                db,
                page=1,
                lab_id=int(lab_id),
                page_size=10,
                keywords=keywords)
            rows = [{
                "id": item.id,
                "name": item.name,
                "lab_id": item.lab_id,
                "lab_name": item.lab_name,
                "spec": item.spec,
                "quantity": item.quantity,
                "status": item.status,
            } for item in page.list]
            return json.dumps({
                "total": page.total,
                "equipments": rows
            },
                              ensure_ascii=False)
        except Exception as exc:
            return json.dumps({
                "ok": False,
                "error": str(exc)
            },
                              ensure_ascii=False)

    @tool(description="创建预约单预约实验室或者设备")
    def create_lab_reservation(lab_id: int,
                               date: str,
                               start_time: str,
                               end_time: str,
                               equipment_id: int | None = None,
                               remark: str | None = None) -> str:
        print(f'[tool] create_lab_reservation lab_id={lab_id} '
              f'equipment_id={equipment_id} date={date} '
              f'{start_time}~{end_time} remark={remark}')
        try:
            data = Reservation(lab_id=lab_id,
                               equipment_id=equipment_id,
                               date=date,
                               start_time=start_time,
                               end_time=end_time,
                               remark=remark)
            reservation_service.create_reservation(db=db,
                                                   current_user=current_user,
                                                   data=data)
            result = json.dumps({
                "ok": True,
                "message": "预约已提交，请等待管理员审核",
                "lab_id": lab_id,
                "equipment_id": equipment_id,
                "date": date,
                "start_time": start_time,
                "end_time": end_time
            },
                              ensure_ascii=False)
        except BussinessException as exc:
            result = json.dumps({
                "ok": False,
                "error": exc.message
            },
                                ensure_ascii=False)
        except Exception as exc:
            traceback.print_exc()
            result = json.dumps({
                "ok": False,
                "error": str(exc)
            },
                                ensure_ascii=False)
        print(f'[tool] create_lab_reservation -> {result}')
        return result
    
    @tool(description="获取服务器当前日期")
    def get_today()->str:
        return datetime.now().strftime('%Y-%m-%d')


    return [search_lab_docs,list_open_labs,list_lab_equipments,create_lab_reservation,get_today]