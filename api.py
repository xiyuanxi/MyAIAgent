import uuid
from datetime import date as _date
from typing import Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, BaseMessage, SystemMessage
from pydantic import BaseModel

from agent import create_agent_executor, WEEKDAYS

app = FastAPI(title="MyAIAgent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_executor = create_agent_executor()
sessions: Dict[str, List[BaseMessage]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())
    history = sessions.setdefault(session_id, [])
    history.append(HumanMessage(content=req.message))
    today = _date.today()
    date_msg = SystemMessage(content=f"今天是 {today.isoformat()}（{WEEKDAYS[today.weekday()]}）。")
    # noinspection PyTypeChecker
    response = agent_executor.invoke({"messages": [date_msg] + history})
    ai_message = response["messages"][-1]
    history.append(ai_message)
    return ChatResponse(reply=ai_message.content, session_id=session_id)


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    existed = session_id in sessions
    sessions.pop(session_id, None)
    return {"ok": existed}
