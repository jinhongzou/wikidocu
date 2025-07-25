import os
import asyncio
from langchain_core.messages import BaseMessage, HumanMessage
from src.graph import create_async_tools_graph

config = {"configurable": {"thread_id": "1"}}

# 主函数
async def main():
    # 创建图实例
    graph = create_async_tools_graph()

    print("欢迎使用检索聊天机器人！输入 'exit' 或 'q' 退出。")

    while True:
        # 初始化参数
        user_input = ''
        input_file_paths = ''

        # 获取研究主题
        while not user_input.strip():
            user_input = input("\n请输入研究主题（或输入 'exit' 退出）: ").strip()

        if user_input.lower() == 'exit':
            print("退出程序。")
            break

        try:

            response = await graph.ainvoke({"messages": [HumanMessage(content=user_input)]
                                            }, config)

            ai_answer = response["messages"][-1]
            print("\n【最终答案】\n")
            print(f"{ai_answer.content}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break

if __name__ == "__main__":
    asyncio.run(main())

