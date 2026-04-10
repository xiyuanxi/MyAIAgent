# Multi-Model Support Design

**Date:** 2026-04-10  
**Status:** Approved

## Overview

Add support for multiple LLM providers (starting with Gemini alongside existing OpenAI) to the MyAIAgent backend. Users can select the model on a per-message basis via the `/chat` API. The frontend exposes a model toggle button.

## Architecture

### Model Selection Granularity

Model is chosen **per message** — each `POST /chat` request carries an optional `model` field. The same session's conversation history (a plain list of `BaseMessage`) is model-agnostic, so switching models mid-session works without any state migration.

### Backend: agent.py

`create_agent_executor(provider: str)` accepts a provider string:

| provider   | LLM class                        | Model              | Package                    |
|------------|----------------------------------|--------------------|----------------------------|
| `"openai"` | `ChatOpenAI`                     | `gpt-4o`           | `langchain-openai` (existing) |
| `"gemini"` | `ChatGoogleGenerativeAI`         | `gemini-2.5-flash` | `langchain-google-genai` (new) |

Both providers use the same tools list and system prompt defined in `_SYSTEM_PROMPT`.

### Backend: api.py

At startup, attempt to initialize each provider. Providers whose API keys are absent are skipped silently:

```python
executors: Dict[str, Any] = {}
for provider in ("openai", "gemini"):
    try:
        executors[provider] = create_agent_executor(provider)
    except Exception:
        pass  # key not configured
```

`ChatRequest` gains an optional field:

```python
class ChatRequest(BaseModel):
    message: str
    session_id: str = ""
    model: str = "openai"
```

Request handler:

```python
executor = executors.get(req.model)
if executor is None:
    raise HTTPException(status_code=400, detail=f"Model '{req.model}' is not available")
```

### Dependencies

- Add to `requirements.txt`: `langchain-google-genai`
- Add to `.env` (local and EC2): `GOOGLE_API_KEY=<key>`

### Frontend: my-ai-frontend

- Add a model toggle (e.g., `OpenAI` / `Gemini` button pair) to the chat UI in `app/page.tsx`
- Selected model stored in React state: `const [model, setModel] = useState("openai")`
- `sendMessage()` in `lib/api.ts` gains a `model` parameter, passes it in the request body
- Next.js proxy route `app/api/chat/route.ts` forwards the field transparently (no change needed as it passes the whole body)

## Data Flow

```
User selects model in UI
  → click Send
  → POST /api/chat { message, session_id, model }
  → Next.js proxy → POST <BACKEND>/chat { message, session_id, model }
  → api.py picks executor from executors[model]
  → agent invoked with session history
  → reply returned
```

## Error Handling

| Scenario                        | Response                                      |
|---------------------------------|-----------------------------------------------|
| Invalid `model` value           | HTTP 400: `"Model 'xyz' is not available"`    |
| Provider key missing at startup | Provider absent from `executors`; same 400    |
| Provider API call fails         | Propagated as HTTP 500 by FastAPI default     |

## Out of Scope

- Persisting the per-session model preference (user can switch per message freely)
- Model-specific system prompt tuning
- Streaming responses
- Adding more providers beyond Gemini in this iteration
