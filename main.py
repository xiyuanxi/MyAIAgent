from datetime import date as _date

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent

from tools import create_tools

# 1. 环境配置
load_dotenv()

# 2. 初始化大脑 (LLM)
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# 3. 构建 Agent (LangGraph ReAct Agent)
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
agent_executor = create_agent(
    model=llm,
    tools=create_tools(),
    system_prompt=system_prompt,
)

# 4. 聊天循环
if __name__ == "__main__":
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
