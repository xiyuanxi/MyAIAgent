# FastAPI Service Design

## Overview

Wrap the existing LangChain/LangGraph CLI Agent as a FastAPI HTTP service so a Next.js frontend can call it. The CLI (`main.py`) continues to work unchanged. Agent initialization logic is extracted into a shared `agent.py` module.

## Architecture

```
MyAIAgent/
  agent.py     ← NEW: create_agent_executor() — shared by CLI and API
  main.py      ← MODIFIED: import from agent.py, CLI loop unchanged
  api.py       ← NEW: FastAPI app, session management, CORS
  tools/       ← unchanged
```

### agent.py

Exports a single function:

```python
def create_agent_executor() -> CompiledGraph:
    ...
```

Initializes GPT-4o LLM, calls `create_tools()`, builds the ReAct agent with system prompt. The system prompt injects today's date **at call time** (not at import time), fixing the stale-date bug.

### main.py

Imports `create_agent_executor` from `agent.py`. CLI loop behavior is identical to current implementation.

### api.py

FastAPI application with:
- CORS middleware (`allow_origins=["*"]` for local development)
- In-memory session store: `Dict[str, List[BaseMessage]]`
- Three endpoints (see below)

## API Endpoints

### `POST /chat`

Send a message and receive a reply.

**Request body:**
```json
{
  "message": "今天苹果股价多少？",
  "session_id": "abc123"
}
```
`session_id` is optional. If omitted, a new UUID is generated and returned.

**Response body:**
```json
{
  "reply": "AAPL 当前股价为 189.50 USD",
  "session_id": "abc123"
}
```

**Behavior:**
1. Look up `session_id` in the session store (create empty list if new)
2. Append `HumanMessage(content=message)` to history
3. Invoke agent with full history
4. Append AI response to history
5. Return reply and session_id

### `DELETE /sessions/{session_id}`

Clear conversation history for a session.

**Response:**
```json
{ "ok": true }
```

Returns `{ "ok": false }` if session_id not found (no error raised).

### `GET /health`

Health check.

**Response:**
```json
{ "status": "ok" }
```

## Session Management

- Store: `sessions: Dict[str, List[BaseMessage]] = {}`
- Key: UUID string (`session_id`)
- Value: list of `HumanMessage` / `AIMessage` objects
- Lifetime: in-memory only, cleared on server restart
- No max session size limit (acceptable for local/dev use)

## CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Allows Next.js dev server (`localhost:3000`) to call the API without proxy configuration.

## Running

```bash
.venv/bin/uvicorn api:app --reload --port 8000
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Dependencies

New packages to add:
- `fastapi`
- `uvicorn[standard]`

## Out of Scope

- Streaming responses
- Persistent session storage
- Authentication
- Rate limiting
- Production deployment configuration
