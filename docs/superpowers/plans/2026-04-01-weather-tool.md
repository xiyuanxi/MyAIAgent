# Weather Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `get_weather` tool to the AI Agent that queries WeatherAPI.com for current weather, forecasts (daily and hourly), and historical data (daily summary and hourly).

**Architecture:** A single `@tool`-decorated function `get_weather` in `tools/weather.py` that uses `requests` to call WeatherAPI.com REST endpoints, routing by `query_type` parameter (`current`, `forecast`, `hourly`, `history`, `hourly_history`). Registered via `create_tools()` in `tools/__init__.py`.

**Tech Stack:** Python, requests, WeatherAPI.com REST API, LangChain `@tool` decorator

---

## File Structure

- **Create:** `tools/weather.py` — `get_weather` tool implementation
- **Modify:** `tools/__init__.py` — import and export `get_weather`
- **Modify:** `.env` — add `WEATHER_API_KEY`
- **Modify:** `main.py` — update system prompt

---

### Task 1: Install dependency and configure API key

- [x] **Step 1: Install requests**

Run: `pip install requests`
Expected: Successfully installed (or "already satisfied")

- [x] **Step 2: Add WEATHER_API_KEY to .env**

Add the following line to `.env`:

```
WEATHER_API_KEY=your_weatherapi_key_here
```

Replace `your_weatherapi_key_here` with an actual API key from https://www.weatherapi.com/

- [x] **Step 3: Verify API key works**

Run:
```bash
python3 -c "
import requests, os
from dotenv import load_dotenv
load_dotenv()
key = os.getenv('WEATHER_API_KEY')
r = requests.get(f'http://api.weatherapi.com/v1/current.json?key={key}&q=London')
print(r.status_code, r.json().get('location', {}).get('name', 'FAILED'))
"
```
Expected: `200 London`

---

### Task 2: Implement get_weather tool function

**Files:**
- Create: `tools/weather.py`

- [x] **Step 1: Create tools/weather.py**

Supports 5 query types: `current`, `forecast`, `hourly`, `history`, `hourly_history`.

- [x] **Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('tools/weather.py').read()); print('OK')"`
Expected: `OK`

---

### Task 3: Register tool and update system prompt

**Files:**
- Modify: `tools/__init__.py`
- Modify: `main.py`

- [x] **Step 1: Add get_weather to tools/__init__.py**

```python
from .weather import get_weather

def create_tools():
    return [create_tavily_search(), get_stock_price, get_stock_history, get_sector_performance, multiply, get_weather]
```

- [x] **Step 2: Update system prompt in main.py**

Add rules:
- "当用户询问天气时，必须调用 get_weather 工具查询，不得自行编造天气信息。"
- "当用户询问未来逐小时天气时，使用 query_type='hourly'。"
- "当用户询问历史某天的逐小时天气时，使用 query_type='hourly_history'。"

- [x] **Step 3: Verify the agent starts without error**

Run: `echo "q" | .venv/bin/python main.py`
Expected: Program starts and exits cleanly without errors.

---

### Task 4: Manual end-to-end test

- [ ] **Step 1: Test current weather**

Run: `.venv/bin/python main.py`
Input: `What's the weather in London?`
Expected: Agent calls `get_weather` with `query_type="current"`, returns current temperature and conditions for London.

- [ ] **Step 2: Test forecast**

Input: `What's the 3-day forecast for Tokyo?`
Expected: Agent calls `get_weather` with `query_type="forecast"`, returns 3-day forecast with dates and temperatures.

- [ ] **Step 3: Test hourly forecast**

Input: `Show me the hourly weather for Beijing today`
Expected: Agent calls `get_weather` with `query_type="hourly"` and `days=1`, returns 24 hourly entries.

- [ ] **Step 4: Test history (daily)**

Input: `What was the weather in New York on 2026-03-01?`
Expected: Agent calls `get_weather` with `query_type="history"` and `date="2026-03-01"`, returns daily summary.

- [ ] **Step 5: Test hourly history**

Input: `Show me the hourly weather in Tokyo on 2026-03-01`
Expected: Agent calls `get_weather` with `query_type="hourly_history"` and `date="2026-03-01"`, returns 24 hourly entries for that day.

- [ ] **Step 6: Test error case**

Input: `What's the weather in asdfghjkl?`
Expected: Agent handles the error gracefully and informs the user.
