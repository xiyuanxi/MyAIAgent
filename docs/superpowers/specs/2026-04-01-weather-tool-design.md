# Weather Tool Design

## Overview

Add a weather query tool to the existing LangChain/LangGraph AI Agent, using WeatherAPI.com as the data source.

## Data Source

- **Provider:** WeatherAPI.com
- **API Key:** Read from `WEATHER_API_KEY` environment variable via `.env`
- **Free tier:** Supports current weather, 3-day forecast (including hourly data), and historical weather

## Tool Interface

A single `get_weather` function using the `@tool` decorator.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `city` | str | Yes | City name (e.g., "Beijing", "New York") |
| `query_type` | str | Yes | `"current"` / `"forecast"` / `"hourly"` / `"history"` |
| `days` | int | No | Forecast days, for `forecast` and `hourly`, default 3, max 3 (free tier) |
| `date` | str | No | Date for history query, format `YYYY-MM-DD` |

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
| `history` | `/v1/history.json` | `q={city}&dt={date}` |

## Integration

### Scope

Only `main.py` is modified. No new files.

### Changes

1. **Add import:** `import requests`
2. **Add tool function:** `get_weather` after existing `multiply` tool
3. **Register tool:** Add `get_weather` to `tools` list
4. **Update system prompt:**
   - Inject today's date dynamically for relative date resolution
   - Add rule: "When the user asks about weather, you must call the get_weather tool"
   - Add rule: "When the user asks for hourly weather, use query_type='hourly'"

### Dependencies

- `requests` (likely already installed)
- `WEATHER_API_KEY` in `.env`

### Unchanged

- LLM choice (GPT-4o)
- Agent creation method (`create_agent`)
- Interactive loop logic