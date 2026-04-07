# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A conversational AI agent built with LangChain/LangGraph that can search the web, check stock prices, query weather, and perform calculations. Uses GPT-4o as the LLM backbone with a ReAct agent pattern.

## Running

```bash
# Activate venv and run
.venv/bin/python main.py
```

Requires `.env` with: `OPENAI_API_KEY`, `TAVILY_API_KEY`, `WEATHER_API_KEY`

## Architecture

- **`main.py`** — 入口：加载环境变量、初始化 LLM、构建 agent、聊天循环
- **`tools/`** — 所有工具模块：
  - `stock.py` — `get_stock_price`（单只股票）、`get_sector_performance`（美股板块 ETF 涨跌幅），均通过 yfinance
  - `weather.py` — `get_weather`（WeatherAPI.com：current/forecast/hourly/history）
  - `math.py` — `multiply`（算术）
  - `search.py` — `create_tavily_search()`（Tavily 网络搜索，延迟实例化以确保环境变量已加载）
  - `__init__.py` — `create_tools()` 汇总导出所有工具列表

Agent 使用 `create_agent()` from `langchain.agents`（LangGraph ReAct），system prompt 强制要求使用工具（股票问题必须搜索、数学必须用 multiply 等）。聊天循环维护 `chat_history` 实现多轮对话。

## Key Constraints

- WeatherAPI free tier: max 3-day forecast. Code allows up to 14 days but API will only return what the plan supports.
- The system prompt injects today's date at import time (`_date.today()`), so the process must be restarted daily to get an updated date.
- Agent input type: LangGraph's `invoke()` expects typed input but accepts dicts — the `# noinspection PyTypeChecker` comment suppresses PyCharm's false positive.