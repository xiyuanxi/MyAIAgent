# FastAPI Service Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wrap the existing LangChain/LangGraph CLI Agent as a FastAPI HTTP service while keeping the CLI intact.

**Architecture:** Extract agent initialization into `agent.py`, update `main.py` to import from it, and create `api.py` with three endpoints, in-memory session management, and CORS support.

**Tech Stack:** Python, FastAPI, uvicorn, LangChain, LangGraph, LangChain-OpenAI

---

## File Structure

- **Create:** `agent.py` — `create_agent_executor()` with dynamic date injection
- **Modify:** `main.py` — import from `agent.py`, remove duplicated agent init code
- **Create:** `api.py` — FastAPI app with CORS, session store, three endpoints
- **Modify:** `requirements.txt` — add fastapi, uvicorn[standard]

---

### Task 1: Install dependencies and update requirements.txt

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Install fastapi and uvicorn**

Run:
```bash
.venv/bin/pip install "fastapi" "uvicorn[standard]"
```
Expected output includes: `Successfully installed fastapi-... uvicorn-...`

- [ ] **Step 2: Capture new versions**

Run:
```bash
.venv/bin/pip show fastapi uvicorn | grep -E "^(Name|Version):"
```
Note the exact versions output.

- [ ] **Step 3: Update requirements.txt**

Add the two lines with the exact versions from Step 2. Final `requirements.txt` should look like:
```
langchain==1.2.13
langchain-openai==1.1.12
langchain-core==1.2.23
langchain-tavily==0.2.17
langgraph==1.1.3
yfinance==1.2.0
requests==2.33.0
python-dotenv==1.2.2
fastapi==<version from step 2>
uvicorn==<version from step 2>
```

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "chore: add fastapi and uvicorn dependencies"
```

---

### Task 2: Create agent.py

**Files:**
- Create: `agent.py`

- [ ] **Step 1: Create agent.py**

```python
from datetime import date as _date

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from tools import create_tools

load_dotenv()


def create_agent_executor():
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    system_prompt = (
        f"你是一个助手。今天的日期是 {_date.today().isoformat()}。"
        "当用户提到'今天'、'昨天'、'上星期'等相对日期时，请根据今天的日期正确推算出具体日期。"
        "当用户询问股票价格等实时信息时，你必须先调用搜索工具查询，不得直接回答说无法获取。"
        "当用户询问某股票最近几天、一周、一个月等历史走势或历史数据时，必须调用 get_stock_history 工具，不得引导用户去外部网站查询。"
        "当用户询问股票排名、涨跌幅排行、市场趋势等综合性问题时，必须先调用搜索工具查询最新信息，再结合 get_stock_price 工具获取具体价格，不得以'无法获取'为由拒绝回答。"
        "当用户询问板块涨跌幅、行业表现、板块排名等问题时，必须调用 get_sector_performance 工具获取实时板块数据。"
        "所有乘法计算，无论多么简单，都必须调用 multiply 工具来完成，不得自行心算。"
        "当用户询问天气时，必须调用 get_weather 工具查询，不得自行编造天气信息。"
        "当用户询问未来逐小时天气时，使用 query_type='hourly'。"
        "当用户询问历史某天的逐小时天气时，使用 query_type='hourly_history'。"
    )
    return create_agent(
        model=llm,
        tools=create_tools(),
        system_prompt=system_prompt,
    )
```

- [ ] **Step 2: Verify syntax**

Run:
```bash
.venv/bin/python -c "import ast; ast.parse(open('agent.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add agent.py
git commit -m "refactor: extract agent initialization into agent.py with dynamic date"
```

---

### Task 3: Update main.py to import from agent.py

**Files:**
- Modify: `main.py`

- [ ] **Step 1: Replace main.py content**

```python
from langchain_core.messages import HumanMessage

from agent import create_agent_executor

if __name__ == "__main__":
    agent_executor = create_agent_executor()
    chat_history = []
    while True:
        user_input = input("\n请输入你的问题（输入 q 退出）：").strip()
        if user_input.lower() == "q":
            break
        if not user_input:
            continue

        chat_history.append(HumanMessage(content=user_input))

        # noinspection PyTypeChecker
        response = agent_executor.invoke({"messages": chat_history})

        ai_message = response["messages"][-1]
        chat_history.append(ai_message)

        print("\n--- 最终回答 ---")
        print(ai_message.content)
```

- [ ] **Step 2: Verify CLI still starts cleanly**

Run:
```bash
echo "q" | .venv/bin/python main.py
```
Expected: program starts and exits without errors.

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "refactor: main.py now imports agent from agent.py"
```

---

### Task 4: Create api.py

**Files:**
- Create: `api.py`

- [ ] **Step 1: Create api.py**

```python
import uuid
from typing import Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage, BaseMessage
from pydantic import BaseModel

from agent import create_agent_executor

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
    # noinspection PyTypeChecker
    response = agent_executor.invoke({"messages": history})
    ai_message = response["messages"][-1]
    history.append(ai_message)
    return ChatResponse(reply=ai_message.content, session_id=session_id)


@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    existed = session_id in sessions
    sessions.pop(session_id, None)
    return {"ok": existed}
```

- [ ] **Step 2: Verify syntax**

Run:
```bash
.venv/bin/python -c "import ast; ast.parse(open('api.py').read()); print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Verify FastAPI app loads**

Run:
```bash
.venv/bin/python -c "from api import app; print('routes:', [r.path for r in app.routes])"
```
Expected output includes: `/health`, `/chat`, `/sessions/{session_id}`

- [ ] **Step 4: Commit**

```bash
git add api.py
git commit -m "feat: add FastAPI service with session management and CORS"
```

---

### Task 5: End-to-end smoke test

- [ ] **Step 1: Start the server**

Run in a terminal:
```bash
.venv/bin/uvicorn api:app --reload --port 8000
```
Expected: `Uvicorn running on http://127.0.0.1:8000`

- [ ] **Step 2: Test health endpoint**

Run in another terminal:
```bash
curl -s http://localhost:8000/health
```
Expected: `{"status":"ok"}`

- [ ] **Step 3: Test chat endpoint**

```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "12 乘以 34 是多少？"}'
```
Expected: JSON with `reply` containing "408" and a `session_id` UUID.

- [ ] **Step 4: Test session continuity**

Copy the `session_id` from Step 3, then:
```bash
curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "再乘以 2 呢？", "session_id": "<session_id_from_step_3>"}'
```
Expected: reply containing "816" (Agent recalls previous result).

- [ ] **Step 5: Test session deletion**

```bash
curl -s -X DELETE http://localhost:8000/sessions/<session_id_from_step_3>
```
Expected: `{"ok":true}`

- [ ] **Step 6: Push to GitHub**

```bash
git push
```
