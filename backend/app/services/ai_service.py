import traceback
from app.services import lab_service
import json
from sqlalchemy.orm import Session
from app.services import kb_service, equipment_service
from app.schemas.ai import ChatMessage
from app.schemas.ai import ChatRequest
from app.common.exceptions import BussinessException
from app.config import settings
from openai import OpenAI

SYSTEM_PROMPT = """你是智能实验室预约系统的助手，回答要简洁。
如果下面提供了实验室资料，请依据资料回答规则、安全、文档里的开放时间说明。
查询当前有哪些开放实验室、某实验室有哪些设备时，必须调用工具，不要编造。
你不能替用户提交预约，也不能直接改数据库。
如果用户要预约，请说明去「实验室列表」选择后提交，等待管理员审核。
"""
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_open_labs",
            "description": "查询当前开放中的实验室列表，可以按名称关键字来筛选",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "实验室的名称关键字，可以为空",
                    }
                },
            },
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_lab_equipments",
            "description": "查询某个实验室下的设备列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "lab_id": {
                        "type": "integer",
                        "description": "实验室 ID",
                    },
                    "keywords": {
                        "type": "string",
                        "description": "设备名称的关键字，可以为空",
                    },
                },
            },
        },
    },
]


def run_tool(db: Session, name: str, arguments: str) -> str:
    try:
        args = json.loads(arguments or "{}")
    except json.JSONDecodeError:
        return json.dumps({"error": "参数不是合法的json"}, ensure_ascii=False)
    try:
        if name == "list_open_labs":
            keywords = (args.get("keywords") or "").strip() or None
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
                "close_time": item.close_time
            } for item in page.list]
            return json.dumps({
                "total": page.total,
                "labs": rows
            },
                              ensure_ascii=False)
        if name == "list_lab_equipments":
            lab_id = args.get("lab_id") or None
            if not lab_id:
                return json.dumps({"error": "参数缺少实验室id"}, ensure_ascii=False)
            keywords = (args.get("keywords") or "").strip() or None
            page = equipment_service.get_equipment_page_list(
                db,
                page=1,
                lab_id=int(lab_id),
                page_size=10,
                keywords=keywords,
            )
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
        return json.dumps({"error": f"未找到工具：{name}"}, ensure_ascii=False)

    except Exception as e:
            return json.dumps({"error": getattr(e, "message", None) or str(e)},
                          ensure_ascii=False)
def get_client() -> OpenAI:
    """获取LLM客户端"""
    if not settings.LLM_API_KEY:
        raise BussinessException(message="LLM_API_KEY is empty")
    return OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )


def chat(db: Session, data: ChatRequest):
    if not data.messages:
        raise BussinessException(message="messages is empty")
    history = []
    for message in data.messages:
        if message.role in ("user", "assistant") and message.content.strip():
            history.append(message)
    if not history:
        raise BussinessException(message="请输入您要对话的内容")
    question = next((item.content
                     for item in reversed(history) if item.role == 'user'), "")
    knowledge = kb_service.search(query=question) if question else ""
    print('检索到向量库内容', knowledge)
    system_prompy = SYSTEM_PROMPT
    if knowledge:
        system_prompy += "\n\n以下是检索到的实验室资料:\n" + knowledge

    client = get_client()
    messages = [ChatMessage(role="system", content=system_prompy), *history]
    try:
        for _ in range(5):
            res = client.chat.completions.create(model=settings.LLM_MODEL,
                                                 messages=messages,
                                                 tools=TOOLS,
                                                 tool_choice='auto')
            msg = res.choices[0].message
            tool_calls = msg.tool_calls or []
            if not tool_calls:  #没有工具调用则直接返回大模型输出结果内容
                content = msg.content
                if not content or not content.strip():
                    raise BussinessException(message="大模型没任何返回内容")
                return content
            messages.append({
                "role":
                "assistant",
                "content":
                msg.content or "",
                "tool_calls": [{
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                } for call in tool_calls]
            })
            for call in tool_calls:
                result = run_tool(db, call.function.name,
                                  call.function.arguments)
                messages.append({
                    "role": "tool",
                    "content": result,
                    "tool_call_id": call.id
                })
        # 关键：达到轮次上限仍未给出文字回答，禁用工具强制收尾，保证永不返回 None
        res = client.chat.completions.create(model=settings.LLM_MODEL,
                                             messages=messages)
        content = res.choices[0].message.content
        if not content or not content.strip():
            raise BussinessException(message="大模型多次查询资料后仍未给出答复，请换个说法重试")
        return content
    except BussinessException:
        raise  # 业务异常直接上抛，别被下面包装成“大模型调用失败”
    except Exception as e:
        traceback.print_exc()
        raise BussinessException(message="大模型调用失败")
