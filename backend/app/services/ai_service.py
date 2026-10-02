from app.schemas.ai import ChatMessage
from app.schemas.ai import ChatRequest
from app.common.exceptions import BussinessException
from app.config import settings
from openai import OpenAI

SYSTEM_PROMPT = """你是智能实验室预约系统的助手，回答要简洁。
你可以介绍本系统的预约流程：
1. 登录后打开实验室列表，选择实验室或设备
2. 填写日期和时段并提交，状态为待审核
3. 管理员审核通过后即可使用
4. 待审核、已通过的预约，本人可以取消
你目前查不到真实的实验室、设备、预约数据。
如果用户问某个实验室几点开门、有没有某台设备，请说明去「实验室列表」查看，不要编造具体数据。
如果用户问了跟实验室无关的问题，可以直接拒绝回答。
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
    client = get_client()
    try:
        res = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                ChatMessage(role="assistant", content=SYSTEM_PROMPT),
                *history
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
    
