from langchain_core.messages import HumanMessage

from agent import create_agent_executor

if __name__ == "__main__":
    agent_executor = create_agent_executor()
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
