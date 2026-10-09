import traceback
from langchain_core.messages import ToolMessage
from typing import Any
from langchain_core.messages import SystemMessage
from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage
from app.common.exceptions import BussinessException
from app.schemas.ai import ChatRequest
from langgraph.constants import END
from langgraph.constants import START
from app.config import settings
from langchain_openai import ChatOpenAI
from app.services import agent_tools
from app.models.user import User
from sqlalchemy.orm import Session
from langgraph.graph import MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

SYSTEM_PROMPT = """你是智能实验室预约系统的 Agent，回答要简洁。
你可以：
1. 使用 search_lab_docs 查询实验室的规则、安全、开放时间等问题
2. 使用 list_open_labs / list_lab_equipments  查询真实的实验室和设备
3. 再用户进行了预约确认后，使用 create_lab_reservation 来进行真实的预约落库
4. 使用 get_today 来进行日期的换算
## 必须遵守
当用户提到了 今天、明天、后天 等日期相关的问题，请先调用 get_today 来获取日期，**不要直接返回 我需要确定明天的具体日期**。
在提交预约之前必须向用户复述：实验室ID与名称（或设备ID和名称）、日期、开始时间、结束时间。并得到用户确认再进行实际操作。
用户没说【确认】【确认预约】【就这样预约】等确定性回复之前，不要调用 create_lab_reservation。
工作流的确认环节里如果缺少了 lab_id，请先 list_open_labs 查到了 lab_id 再创建，不要瞎写。
工作流的确认环节里如果缺少了 equipment_id，请先 list_lab_equipments 查到了 equipment_id 再创建，不要瞎写。
预约成功后状态是待审核，必须管理员确认后实验室（或设备）才能使用。
不要瞎编数据库里没有的实验室或者设备信息。
如果是问开放时间或者实验室规则，优先调用 search_lab_docs，不要凭空回复。
## 工具结果处理
工具返回的 json 里如果 ok 为 false，说明这次操作失败了，必须把 error 里的原因如实告诉用户，
禁止在工具失败的情况下回复「预约成功」这类话术。
只有 create_lab_reservation 返回 ok 为 true 时，才能告诉用户预约已提交、等待管理员审核。
"""
TOOL_LABELS = {
    "search_lab_docs": "检索实验室知识库",
    "list_open_labs": "查询开发实验室",
    "list_lab_equipments": "查询实验室设备",
    "create_lab_reservation": "创建预约单",
    "get_today": "获取今天日期"
}


def build_agent(db: Session, current_user: User):
    tools = agent_tools.build_tools(db, current_user)
    llm = ChatOpenAI(api_key=settings.LLM_API_KEY,
                     base_url=settings.LLM_BASE_URL,
                     model=settings.LLM_MODEL,
                     temperature=0,
                     streaming=True).bind_tools(tools)

    async def agent_node(state: MessagesState):
        response = await llm.ainvoke(state["messages"])
        print('[agent]:', response)
        if response.tool_calls:
            print('[agent] 请求调用工具:', [(call["name"], call["args"])
                                      for call in response.tool_calls])
        else:
            print('[agent] 直接回复文本:', response.content)
        return {"messages": [response]}

    graph = StateGraph(state_schema=MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")
    return graph.compile()


def _build_history(data: ChatRequest) -> list:
    history = []
    for message in data.messages:
        if message.role == 'user' and message.content.strip():
            history.append(HumanMessage(content=message.content.strip()))
        elif message.role == 'assistant' and message.content.strip():
            history.append(AIMessage(content=message.content.strip()))
    if not history:
        raise BussinessException(message='请输入您的对话内容')
    return history


def _tool_output_preview(output: Any, limit: int = 200):
    if isinstance(output, ToolMessage):
        output = output.content
    text = output if isinstance(output, str) else str(output)
    return text if len(text) <= limit else text[:limit] + "..."


def _chunk_text(chunk: Any):
    """从模型的流式输出拿到纯文本"""
    if chunk is None:
        return ""
    #chunk如果是AIMessage ,则可以取content
    content = getattr(chunk, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for part in content:
            if isinstance(part, str):
                parts.append(part)
            elif isinstance(part, dict):
                parts.append(part.get("text") or "")
        return "".join(parts)
    return str(content) if content is not None else ""
async def stream_agent(db: Session, current_user: User, data: ChatRequest):
    """流式输出生成器 边跑agent边yield"""
    try:
        history = _build_history(data)
        agent = build_agent(db, current_user)
        inputs = {"messages": [SystemMessage(content=SYSTEM_PROMPT), *history]}
        yield {"type": "status", "message": "正在思考..."}
        async for event in agent.astream_events(inputs,
                                         config={"recursion_limit": 10}):
            kind = event.get("event")
            if kind == "on_tool_start":
                name = event.get('name') or ''
                yield {
                    "type": "tool_start",
                    "name": name,
                    "label": TOOL_LABELS.get(name, name)
                }
            elif kind == "on_tool_end":
                name = event.get('name') or ''
                yield {
                    "type":
                    "tool_end",
                    "name":
                    name,
                    "label":
                    TOOL_LABELS.get(name, name),
                    "preview":
                    _tool_output_preview((event.get("data")
                                          or {}).get('output'))
                }
            elif kind == "on_chat_model_stream":
                metadata = event.get('metadata') or {}
                if metadata.get("langgraph_node") not in (None, "agent"):
                    continue
                text = _chunk_text((event.get("data") or {}).get('chunk'))
                yield {
                    "type": "token",
                    "content": text
                }
        yield {"type":"done"}
    except BussinessException as e:
        yield {"type": "error", "message": e.message}
    except Exception as e:
        traceback.print_exc()
        yield {"type": "error", "message": "大模型调用失败，请稍后重试"}


# def run_agent(db: Session, current_user: User, data: ChatRequest):
#     if not data.messages:
#         raise BussinessException(message="messages is empty")
#     history = []
#     for message in data.messages:
#         if message.role == 'user' and message.content.strip():
#             history.append(HumanMessage(content=message.content.strip()))
#         elif message.role == 'assistant' and message.content.strip():
#             history.append(AIMessage(content=message.content.strip()))
#     if not history:
#         raise BussinessException(message="请输入您要对话的内容")
#     agent = build_agent(db, current_user)
#     try:
#         result = agent.invoke(
#             {"messages": [SystemMessage(content=SYSTEM_PROMPT), *history]},
#             config={"recursion_limit": 10})  #最多10轮
#     except BussinessException:
#         raise
#     except Exception:
#         raise BussinessException(message="大模型调用失败，请稍后重试")

#     messages = result.get("messages") or []
#     print('messages', messages)
#     if not messages:
#         raise BussinessException(message="大模型没有任何返回内容")
#     for message in reversed(messages):
#         if isinstance(message, AIMessage) and message.content.strip():
#             content = message.content.strip()
#             if isinstance(content, list):
#                 content = "".join(
#                     part.get("text", "") if isinstance(part, dict
#                                                        ) else str(part)
#                     for part in content)
#             if str(content).strip():
#                 return str(content).strip()
