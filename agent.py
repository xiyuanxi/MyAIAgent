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
