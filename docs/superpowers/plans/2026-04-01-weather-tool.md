# Weather Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `get_weather` tool to the AI Agent that queries WeatherAPI.com for current weather, forecasts (daily and hourly), and historical data.

**Architecture:** A single `@tool`-decorated function `get_weather` that uses `requests` to call WeatherAPI.com REST endpoints, routing by `query_type` parameter (`current`, `forecast`, `hourly`, `history`). Integrated into the existing `main.py` alongside existing tools.

**Tech Stack:** Python, requests, WeatherAPI.com REST API, LangChain `@tool` decorator

---

## File Structure

- **Modify:** `main.py` — add `import requests`, add `get_weather` tool function, register in tools list, update system prompt
- **Modify:** `.env` — add `WEATHER_API_KEY`

No new files are created.

---

### Task 1: Install dependency and configure API key

**Files:**
- Modify: `.env` (add `WEATHER_API_KEY`)

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
source .env 2>/dev/null; python3 -c "
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
- Modify: `main.py:1` (add import)
- Modify: `main.py:29` (add function after `multiply`)

- [x] **Step 1: Add import**

Add `import requests` at the top of `main.py`, after the existing imports:

```python
import os
import requests
import yfinance as yf
```

- [x] **Step 2: Add get_weather function**

Add the following after the `multiply` function. Supports 4 query types: `current`, `forecast`, `hourly`, `history`.

```python
@tool
def get_weather(city: str, query_type: str, days: int = 3, date: str = "") -> str:
    """Query weather information for a city.

    Args:
        city: City name, e.g. "Beijing", "New York", "London"
        query_type: One of "current", "forecast", "hourly", or "history"
        days: Number of forecast days (1-3), used when query_type is "forecast" or "hourly"
        date: Date in YYYY-MM-DD format, only used when query_type is "history"
    """
    print(f"[Tool Called] get_weather(city={city}, query_type={query_type})")
    api_key = os.getenv("WEATHER_API_KEY")
    if not api_key:
        return "Error: WEATHER_API_KEY is not configured. Please set it in your .env file."
    base_url = "http://api.weatherapi.com/v1"

    try:
        if query_type == "current":
            resp = requests.get(f"{base_url}/current.json", params={"key": api_key, "q": city}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            c = data["current"]
            return f"{data['location']['name']}: {c['temp_c']}°C, {c['condition']['text']}, Humidity {c['humidity']}%, Wind {c['wind_kph']} km/h"

        elif query_type == "forecast":
            days = min(max(days, 1), 3)
            resp = requests.get(f"{base_url}/forecast.json", params={"key": api_key, "q": city, "days": days}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            lines = [f"{data['location']['name']} {days}-day forecast:"]
            for day in data["forecast"]["forecastday"]:
                d = day["day"]
                lines.append(f"- {day['date']}: {d['maxtemp_c']}°C/{d['mintemp_c']}°C, {d['condition']['text']}")
            return "\n".join(lines)

        elif query_type == "hourly":
            days = min(max(days, 1), 3)
            resp = requests.get(f"{base_url}/forecast.json", params={"key": api_key, "q": city, "days": days}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            lines = [f"{data['location']['name']} hourly forecast ({days} day(s)):"]
            for day in data["forecast"]["forecastday"]:
                lines.append(f"\n[{day['date']}]")
                for hour in day["hour"]:
                    time_str = hour["time"].split(" ")[1]
                    lines.append(
                        f"  {time_str} | {hour['temp_c']}°C | {hour['condition']['text']} | "
                        f"Humidity {hour['humidity']}% | Wind {hour['wind_kph']} km/h | "
                        f"Rain {hour['chance_of_rain']}%"
                    )
            return "\n".join(lines)

        elif query_type == "history":
            if not date:
                return "Error: 'date' parameter is required for history queries (format: YYYY-MM-DD)"
            resp = requests.get(f"{base_url}/history.json", params={"key": api_key, "q": city, "dt": date}, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            day = data["forecast"]["forecastday"][0]["day"]
            return f"{data['location']['name']} on {date}: {day['maxtemp_c']}°C/{day['mintemp_c']}°C, {day['condition']['text']}, Humidity {day['avghumidity']}%"

        else:
            return f"Error: Unknown query_type '{query_type}'. Use 'current', 'forecast', 'hourly', or 'history'."

    except requests.HTTPError as e:
        return f"Weather API error for {city}: HTTP {e.response.status_code}"
    except requests.RequestException as e:
        return f"Unable to reach weather service for {city}: {type(e).__name__}"
```

- [x] **Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('main.py').read()); print('OK')"`
Expected: `OK`

---

### Task 3: Register tool and update system prompt

**Files:**
- Modify: `main.py` (tools list)
- Modify: `main.py` (system_prompt)

- [x] **Step 1: Add get_weather to tools list**

```python
tools = [TavilySearch(max_results=3), get_stock_price, multiply, get_weather]
```

- [x] **Step 2: Update system prompt**

```python
from datetime import date as _date
system_prompt = (
    f"你是一个助手。今天的日期是 {_date.today().isoformat()}。"
    "当用户提到'今天'、'昨天'、'上星期'等相对日期时，请根据今天的日期正确推算出具体日期。"
    "当用户询问股票价格等实时信息时，你必须先调用搜索工具查询，不得直接回答说无法获取。"
    "所有乘法计算，无论多么简单，都必须调用 multiply 工具来完成，不得自行心算。"
    "当用户询问天气时，必须调用 get_weather 工具查询，不得自行编造天气信息。"
    "当用户询问逐小时天气时，使用 query_type='hourly'。"
)
```

- [x] **Step 3: Verify the agent starts without error**

Run: `echo "q" | python3 main.py`
Expected: Program starts and exits cleanly without errors.

- [x] **Step 4: Commit**

```bash
git add main.py
git commit -m "feat: add weather query tool using WeatherAPI.com"
```

---

### Task 4: Manual end-to-end test

- [ ] **Step 1: Test current weather**

Run: `python3 main.py`
Input: `What's the weather in London?`
Expected: Agent calls `get_weather` with `query_type="current"`, returns current temperature and conditions for London.

- [ ] **Step 2: Test forecast**

Input: `What's the 3-day forecast for Tokyo?`
Expected: Agent calls `get_weather` with `query_type="forecast"`, returns 3-day forecast with dates and temperatures.

- [ ] **Step 3: Test hourly forecast**

Input: `Show me the hourly weather for Beijing today`
Expected: Agent calls `get_weather` with `query_type="hourly"` and `days=1`, returns 24 hourly entries with temperature, condition, humidity, wind, and rain chance.

- [ ] **Step 4: Test history**

Input: `What was the weather in New York on 2026-03-01?`
Expected: Agent calls `get_weather` with `query_type="history"` and `date="2026-03-01"`, returns historical weather data.

- [ ] **Step 5: Test error case**

Input: `What's the weather in asdfghjkl?`
Expected: Agent handles the error gracefully and informs the user.