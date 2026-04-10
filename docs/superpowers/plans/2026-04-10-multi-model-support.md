# Multi-Model Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Gemini support alongside OpenAI so callers can choose the LLM provider per request, defaulting to OpenAI.

**Architecture:** `create_agent_executor(provider)` in `agent.py` builds a provider-specific LLM but shares the same tools and system prompt. `api.py` pre-initializes both executors at startup into a dict and dispatches each request to the right one based on the `model` field in `ChatRequest`. The frontend adds a two-button toggle that passes the selected model on every send.

**Tech Stack:** Python/FastAPI backend, `langchain-google-genai` for Gemini, Next.js/React frontend with Tailwind CSS.

---

## File Map

| Action   | Path                                                    | What changes                                       |
|----------|---------------------------------------------------------|----------------------------------------------------|
| Modify   | `agent.py`                                              | Accept `provider` param, add Gemini branch         |
| Modify   | `api.py`                                                | Executors dict, `model` field in `ChatRequest`     |
| Modify   | `requirements.txt`                                      | Add `langchain-google-genai`                       |
| Modify   | `my-ai-frontend/lib/api.ts`                             | Add `model` param to `sendMessage()`               |
| Modify   | `my-ai-frontend/app/page.tsx`                           | Model toggle state + UI + pass model to sendMessage|

---

## Task 1: Add `langchain-google-genai` dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add package to requirements.txt**

  Open `requirements.txt` and append one line:

  ```
  langchain-google-genai
  ```

  (No version pin yet — we'll pin after verifying the compatible version installs cleanly.)

- [ ] **Step 2: Install locally and note the resolved version**

  ```bash
  .venv/bin/pip install langchain-google-genai
  ```

  After install, run:

  ```bash
  .venv/bin/pip show langchain-google-genai | grep Version
  ```

  Note the version printed (e.g. `2.1.4`). Update `requirements.txt` to pin it:

  ```
  langchain-google-genai==<version>
  ```

- [ ] **Step 3: Commit**

  ```bash
  git add requirements.txt
  git commit -m "feat: add langchain-google-genai dependency"
  ```

---

## Task 2: Extend `agent.py` to support multiple providers

**Files:**
- Modify: `agent.py`

- [ ] **Step 1: Replace the file contents**

  The full new `agent.py`:

  ```python
  from dotenv import load_dotenv
  from langchain_openai import ChatOpenAI
  from langchain_google_genai import ChatGoogleGenerativeAI
  from langchain.agents import create_agent

  from tools import create_tools

  load_dotenv()

  WEEKDAYS = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]

  _SYSTEM_PROMPT = (
      "你是一个助手。"
      "在回复中涉及日期时，请同时显示星期几。"
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


  def create_agent_executor(provider: str = "openai"):
      if provider == "gemini":
          llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
      else:
          llm = ChatOpenAI(model="gpt-4.1", temperature=0)
      return create_agent(
          model=llm,
          tools=create_tools(),
          system_prompt=_SYSTEM_PROMPT,
      )
  ```

- [ ] **Step 2: Smoke-test the import**

  ```bash
  .venv/bin/python -c "from agent import create_agent_executor; print('OK')"
  ```

  Expected output: `OK`

- [ ] **Step 3: Commit**

  ```bash
  git add agent.py
  git commit -m "feat: support multiple LLM providers in create_agent_executor"
  ```

---

## Task 3: Update `api.py` — executors dict + `model` field

**Files:**
- Modify: `api.py`

- [ ] **Step 1: Replace the file contents**

  The full new `api.py`:

  ```python
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
  ```

- [ ] **Step 2: Verify startup logs with curl**

  Start the server:

  ```bash
  .venv/bin/uvicorn api:app --port 8000
  ```

  Expected startup output (both or one depending on which keys are in `.env`):
  ```
  [startup] openai executor ready
  [startup] gemini executor ready
  ```

  In another terminal, check health:

  ```bash
  curl http://localhost:8000/health
  ```

  Expected: `{"status":"ok","models":["openai","gemini"]}`

- [ ] **Step 3: Test invalid model returns 400**

  ```bash
  curl -s -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"message":"hi","model":"invalid"}' | python3 -m json.tool
  ```

  Expected: HTTP 400 with `"detail"` containing `"not available"`.

- [ ] **Step 4: Commit**

  ```bash
  git add api.py
  git commit -m "feat: pre-initialize executor pool and add model field to ChatRequest"
  ```

---

## Task 4: Add `GOOGLE_API_KEY` to environment

**Files:**
- `.env` (local, not committed)
- EC2: set via SSH

- [ ] **Step 1: Add key to local `.env`**

  Open `.env` and add:

  ```
  GOOGLE_API_KEY=<your_google_ai_studio_key>
  ```

  Get the key from: https://aistudio.google.com/app/apikey

- [ ] **Step 2: Add key to EC2**

  SSH into EC2 and edit the env file used by systemd:

  ```bash
  sudo nano /etc/myaiagent.env
  ```

  Add:
  ```
  GOOGLE_API_KEY=<your_google_ai_studio_key>
  ```

  Then restart the service:

  ```bash
  sudo systemctl restart myaiagent
  sudo journalctl -u myaiagent -n 20
  ```

  Expected: both `[startup] openai executor ready` and `[startup] gemini executor ready` in logs.

  *(No git commit for this task — keys are not committed.)*

---

## Task 5: Update `lib/api.ts` — add `model` param to `sendMessage`

**Files:**
- Modify: `my-ai-frontend/lib/api.ts`

- [ ] **Step 1: Replace the file contents**

  ```typescript
  export interface ChatResponse {
    reply: string;
    session_id: string;
  }

  export async function sendMessage(
    message: string,
    sessionId: string,
    model: string = "openai"
  ): Promise<ChatResponse> {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, session_id: sessionId, model }),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
  }

  export async function clearSession(sessionId: string): Promise<void> {
    await fetch(`/api/sessions/${sessionId}`, { method: "DELETE" });
  }
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add lib/api.ts
  git commit -m "feat: pass model param in sendMessage"
  ```

---

## Task 6: Add model toggle to `app/page.tsx`

**Files:**
- Modify: `my-ai-frontend/app/page.tsx`

- [ ] **Step 1: Replace the file contents**

  Key changes vs current: add `model` state, add toggle buttons in the input bar, pass `model` to `sendMessage`.

  ```tsx
  "use client";

  import { useState, useRef, useEffect } from "react";
  import ReactMarkdown from "react-markdown";
  import remarkGfm from "remark-gfm";
  import { sendMessage, clearSession } from "@/lib/api";

  interface Message {
    role: "user" | "assistant";
    content: string;
  }

  export default function Home() {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState("");
    const [model, setModel] = useState("openai");
    const bottomRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    async function handleSend() {
      const text = input.trim();
      if (!text || loading) return;

      setInput("");
      setMessages((prev) => [...prev, { role: "user", content: text }]);
      setLoading(true);

      try {
        const data = await sendMessage(text, sessionId, model);
        setSessionId(data.session_id);
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: data.reply },
        ]);
      } catch {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", content: "请求失败，请检查后端服务是否启动。" },
        ]);
      } finally {
        setLoading(false);
      }
    }

    async function handleClear() {
      if (sessionId) await clearSession(sessionId);
      setMessages([]);
      setSessionId("");
    }

    return (
      <div className="flex flex-col h-screen bg-gray-50">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 bg-white border-b shadow-sm">
          <h1 className="text-lg font-semibold text-gray-800">AI Agent</h1>
          <button
            onClick={handleClear}
            className="text-sm text-gray-500 hover:text-red-500 transition-colors"
          >
            清空对话
          </button>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {messages.length === 0 && (
            <p className="text-center text-gray-400 mt-20">
              可以问我股票、天气、计算等问题
            </p>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-blue-500 text-white rounded-br-sm"
                    : "bg-white text-gray-800 shadow-sm border rounded-bl-sm"
                }`}
              >
                {msg.role === "user" ? (
                  msg.content
                ) : (
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                      ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                      ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
                      strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                      code: ({ children }) => <code className="bg-gray-100 rounded px-1 py-0.5 text-xs font-mono">{children}</code>,
                      pre: ({ children }) => <pre className="bg-gray-100 rounded p-2 overflow-x-auto text-xs font-mono mb-2">{children}</pre>,
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                )}
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-white border shadow-sm rounded-2xl rounded-bl-sm px-4 py-3">
                <span className="flex gap-1">
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:300ms]" />
                </span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-4 py-4 bg-white border-t">
          <div className="flex flex-col gap-2 max-w-3xl mx-auto">
            {/* Model toggle */}
            <div className="flex gap-1">
              {["openai", "gemini"].map((m) => (
                <button
                  key={m}
                  onClick={() => setModel(m)}
                  className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
                    model === m
                      ? "bg-blue-500 text-white"
                      : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                  }`}
                >
                  {m === "openai" ? "OpenAI" : "Gemini"}
                </button>
              ))}
            </div>
            {/* Input row */}
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
                placeholder="输入问题，按 Enter 发送..."
                disabled={loading}
                className="flex-1 rounded-xl border border-gray-300 px-4 py-2.5 text-sm text-gray-900 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-gray-100"
              />
              <button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="rounded-xl bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-5 py-2.5 text-sm font-medium transition-colors"
              >
                发送
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
  ```

- [ ] **Step 2: Verify it builds**

  ```bash
  cd /path/to/my-ai-frontend
  npm run build
  ```

  Expected: no TypeScript errors, build succeeds.

- [ ] **Step 3: Commit**

  ```bash
  git add app/page.tsx
  git commit -m "feat: add model toggle (OpenAI / Gemini) to chat UI"
  ```

---

## Task 7: Push both repos and verify end-to-end

- [ ] **Step 1: Push backend**

  ```bash
  cd /path/to/MyAIAgent
  git push origin develop
  ```

  Watch GitHub Actions run (https://github.com/xiyuanxi/MyAIAgent/actions). Wait for green checkmark.

- [ ] **Step 2: Verify EC2 has both models**

  ```bash
  curl http://18.219.18.249:8000/health
  ```

  Expected: `{"status":"ok","models":["openai","gemini"]}`

  If `gemini` is missing, SSH into EC2 and check `sudo journalctl -u myaiagent -n 30` for the skip reason (likely missing `GOOGLE_API_KEY`).

- [ ] **Step 3: Push frontend**

  ```bash
  cd /path/to/my-ai-frontend
  git push origin main
  ```

  Wait for Amplify to redeploy (a few minutes).

- [ ] **Step 4: End-to-end test in browser**

  Open the Amplify URL. Confirm:
  - OpenAI button is selected by default
  - Sending a message works with OpenAI
  - Switching to Gemini and sending a message works
  - Switching back to OpenAI in the same session works
