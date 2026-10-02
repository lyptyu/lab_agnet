from app.services import kb_service
from app.schemas.ai import ChatMessage
from app.schemas.ai import ChatRequest
from app.common.exceptions import BussinessException
from app.config import settings
from openai import OpenAI

SYSTEM_PROMPT = """你是智能实验室预约系统的助手，回答要简洁。
如果下面提供了实验室资料，请依据资料回答，不要编造资料里没有的时间、规则、设备。
你目前查不到真实的实验室空闲、设备库存、预约记录。
如果用户问现在哪些实验室能约、某台设备此刻有没有空，请说明去「实验室列表」查看。
除了实验室相关的问题之外，不要回复无关的问题。
"""


def get_client() -> OpenAI:
    """获取LLM客户端"""
    if not settings.LLM_API_KEY:
        raise BussinessException(message="LLM_API_KEY is empty")
    return OpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL,
    )


def chat(data: ChatRequest):
    if not data.messages:
        raise BussinessException(message="messages is empty")
    history = []
    for message in data.messages:
        if message.role in ("user", "assistant") and message.content.strip():
            history.append(message)
    if not history:
        raise BussinessException(message="请输入您要对话的内容")
    question = next((item.content
                     for item in reversed(history) if item.role == 'user'),
                    "")
    knowledge = kb_service.search(query=question) if question else ""
    print('检索到向量库内容', knowledge)
    system_prompy = SYSTEM_PROMPT
    if knowledge:
        system_prompy += "\n\n以下是检索到的实验室资料:\n" + knowledge

    client = get_client()
    try:
        res = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                ChatMessage(role="system", content=system_prompy), *history
            ],
        )
        print('res', res)
        content = res.choices[0].message.content
        if not content.strip():
            raise BussinessException(message="大模型没任何返回内容")
        return content
    except Exception as e:
        print("e is", e)
        raise BussinessException(message="大模型调用失败")
