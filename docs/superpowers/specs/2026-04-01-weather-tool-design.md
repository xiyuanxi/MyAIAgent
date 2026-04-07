# Weather Tool Design

## Overview

Add a weather query tool to the existing LangChain/LangGraph AI Agent, using WeatherAPI.com as the data source.

## Data Source

- **Provider:** WeatherAPI.com
- **API Key:** Read from `WEATHER_API_KEY` environment variable via `.env`
- **Free tier:** Supports current weather, 3-day forecast (including hourly data), and historical weather. `days` parameter accepts up to 14, but free tier will only return what the plan supports.

## Tool Interface

A single `get_weather` function using the `@tool` decorator, located in `tools/weather.py`.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `city` | str | Yes | City name (e.g., "Beijing", "New York") |
| `query_type` | str | Yes | `"current"` / `"forecast"` / `"hourly"` / `"history"` / `"hourly_history"` |
| `days` | int | No | Forecast days, for `forecast` and `hourly`, default 3, max 14 (free tier returns up to 3) |
| `date` | str | No | Date for `history` or `hourly_history` query, format `YYYY-MM-DD` |

### Return Value

Formatted English string with key weather info (temperature, condition, humidity, wind speed).

**Current example:**
```
Beijing: 25°C, Sunny, Humidity 40%, Wind 12 km/h
```

**Forecast example:**
```
Beijing 3-day forecast:
- 2026-04-01: 25°C/18°C, Sunny
- 2026-04-02: 22°C/16°C, Partly cloudy
- 2026-04-03: 20°C/14°C, Light rain
```

**Hourly example:**
```
Beijing hourly forecast (1 day(s)):

[2026-04-01]
  00:00 | 12.3°C | Clear | Humidity 45% | Wind 8.2 km/h | Rain 0%
  01:00 | 11.8°C | Clear | Humidity 47% | Wind 7.5 km/h | Rain 0%
  ...
```

**History example:**
```
Beijing on 2026-03-01: 22°C/10°C, Sunny, Humidity 35%
```

**Hourly history example:**
```
Beijing hourly history for 2026-03-01:
  00:00 | 10.2°C | Clear | Humidity 50% | Wind 5.0 km/h
  01:00 | 9.8°C | Clear | Humidity 52% | Wind 4.5 km/h
  ...
```

**Error handling:**
- Missing API Key: Returns `"Error: WEATHER_API_KEY is not configured. Please set it in your .env file."`
- HTTP errors: Returns `"Weather API error for {city}: HTTP {status_code}"`
- Network errors: Returns `"Unable to reach weather service for {city}: {exception_type}"`
- All requests use `timeout=10` seconds

## API Endpoint Mapping

| query_type | Endpoint | Key Params |
|------------|----------|------------|
| `current` | `/v1/current.json` | `q={city}` |
| `forecast` | `/v1/forecast.json` | `q={city}&days={days}` |
| `hourly` | `/v1/forecast.json` | `q={city}&days={days}` (parses `hour` array) |
| `history` | `/v1/history.json` | `q={city}&dt={date}` (daily summary) |
| `hourly_history` | `/v1/history.json` | `q={city}&dt={date}` (parses `hour` array) |

## Integration

### File Structure

Tools are organized as a package under `tools/`:

- `tools/weather.py` — `get_weather`
- `tools/stock.py` — `get_stock_price`, `get_stock_history`, `get_sector_performance`
- `tools/math.py` — `multiply`
- `tools/search.py` — `create_tavily_search()`
- `tools/__init__.py` — `create_tools()` exports all tools

### System Prompt Rules

- "当用户询问天气时，必须调用 get_weather 工具查询，不得自行编造天气信息。"
- "当用户询问未来逐小时天气时，使用 query_type='hourly'。"
- "当用户询问历史某天的逐小时天气时，使用 query_type='hourly_history'。"

### Dependencies

- `requests`
- `WEATHER_API_KEY` in `.env`
