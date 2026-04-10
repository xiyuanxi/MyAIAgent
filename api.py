import uuid
from datetime import date as _date
from typing import Dict, List, Any

from fastapi import FastAPI, HTTPException
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

executors: Dict[str, Any] = {}
for _provider in ("openai", "gemini"):
    try:
        executors[_provider] = create_agent_executor(_provider)
        print(f"[startup] {_provider} executor ready")
    except Exception as e:
        print(f"[startup] {_provider} executor skipped: {e}")

sessions: Dict[str, List[BaseMessage]] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str = ""
    model: str = "openai"


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.get("/health")
def health():
    return {"status": "ok", "models": list(executors.keys())}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    executor = executors.get(req.model)
    if executor is None:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{req.model}' is not available. Available: {list(executors.keys())}",
        )
    session_id = req.session_id or str(uuid.uuid4())
    history = sessions.setdefault(session_id, [])
    history.append(HumanMessage(content=req.message))
    today = _date.today()
    date_msg = SystemMessage(content=f"今天是 {today.isoformat()}（{WEEKDAYS[today.weekday()]}）。")
    # noinspection PyTypeChecker
    response = executor.invoke({"messages": [date_msg] + history})
    ai_message = response["messages"][-1]
    history.append(ai_message)
    return ChatResponse(reply=ai_message.content, session_id=session_id)


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    existed = session_id in sessions
    sessions.pop(session_id, None)
    return {"ok": existed}
