
import os
import asyncio
from datetime import datetime
import logging

from typing import Annotated, Dict, Any, List
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode,tools_condition
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from IPython.display import display, Image

from .state import OverallState, QueryGenerationState
from .tools_and_schemas import SearchQueryList
from .filecontentextract import FileContentExtract
from .prompts_zh import final_answer_instructions, general_doc_retrieval_prompt
from .func_utils import get_current_date, get_research_topic
from global_vars import ui_detail_output_handler

interaction_turns=0

# 创建 checkpointer
checkpointer = MemorySaver()

# Nodes (这些节点函数现在需要接收 LLM 实例作为参数，或在内部通过其他方式获取)
# 为了简化，我们假设这些节点可以直接访问到通过 create_async_tools_graph 传入的 LLM 实例
# 或者，我们修改它们的定义，使其接受 LLM 作为参数。
# 这里采用后者，修改函数签名。

def generate_research_topic(state: OverallState, com_llm) -> QueryGenerationState:
    """LangGraph node that generates search queries based on the User's question."""
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = 3

    structured_llm = com_llm.with_structured_output(SearchQueryList)

    current_date = get_current_date()
    chat_messages=state["messages"]
    question=state["messages"][-1].content

    formatted_prompt = general_doc_retrieval_prompt.format(
        current_date=current_date,
        research_topic=chat_messages,
        number_queries=state["initial_search_query_count"],
    )
    result = structured_llm.invoke(formatted_prompt)
    
    search_queries = result.query

    if isinstance(search_queries, list) and len(search_queries) > 0 and search_queries[-1].strip() != "":
        search_query= f"问题:{question}。 关键点：" + ', '.join(search_queries)

        ui_detail_output_handler._turns=ui_detail_output_handler._turns+1
        ui_detail_output_handler.write_content(f"---\n### 第 [{ui_detail_output_handler._turns}] 轮检索\n### [输入问题]:\n{question}\n### [增强检索]:\n{search_query}\n")

        return {"search_query": [search_query]}

    else:
         return {"search_query": []}

async def chatbox3(state: OverallState, com_llm):
    """处理用户查询，决定是否需要调用工具"""
    user_message = state["messages"]

    system_prompt =  """你是一个乐于助人的助手，具备跨文档智能问答、深度知识理解与上下文感知交互的能力。请根据历史对话记录，并结合当前问题，从提供的文档中准确、全面地提取信息进行回答。无需依赖索引，直接基于文档内容和上下文理解给出清晰、有条理的解答。"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{human}"),
    ])
    chain = prompt | com_llm
    response = await chain.ainvoke({"human": user_message})

    return {"messages": response,
            'web_research_result': []
            }

import functools
from typing import Any, Callable

# 工具函数：用于包装异步节点，确保返回 await 后的 dict
async def async_node_wrapper(async_func: Callable, *args, **kwargs) -> Any:
    return await async_func(*args, **kwargs)

# 修改节点定义：添加参数
async def chatbox(state: OverallState, com_llm) -> dict:
    user_message = state["messages"]
    system_prompt = """你是一个乐于助人的助手..."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{human}"),
    ])
    chain = prompt | com_llm
    response = await chain.ainvoke({"human": user_message})
    return {"messages": [response], "web_research_result": []}

async def file_research(state: OverallState, com_llm, api_key, base_url, model_name) -> dict:
    """
    使用本地文件内容检索机制，根据当前状态中的 search_query 执行文件内容搜索。
    """
    if state.get("search_query"):
        research_topic = state["search_query"][-1]

    print(f"工具调用：searcher ({research_topic})")

    researcher = FileContentExtract(
        model=model_name,
        api_key=api_key,
        api_base=base_url,
        name='ResearcherAgent'
    )
    file_path= '.\\docs'
    ui_detail_output_handler.write_content(f"### Scanning the files: \n{file_path}....")

    all_results = await researcher.async_run(
        file_paths=[os.path.abspath(file_path.replace('\\', os.sep).replace('/', os.sep))],
        research_topic=research_topic
    )

    content_md = researcher.get_markdown_ref()

    ui_detail_output_handler.write_content(f"### [检索结果]:\n{content_md}\n")


    return {
        'search_query': [research_topic],
        'web_research_result': [content_md]
    }
async def final_answer(state: OverallState, com_llm):
    """处理用户查询，生成最终答案"""
    research_topic=state["messages"][-1].content

    if state.get("web_research_result"):
        context= state["web_research_result"][-1]

    answer_prompt = ChatPromptTemplate.from_messages([
        ("system", final_answer_instructions),
        ("human", "[ ## 上下文 ## ]\n{context}"),
    ])

    filled_prompt = answer_prompt.invoke({
        "context": context,
        "research_topic": research_topic
    })

    llm_response = await com_llm.ainvoke(filled_prompt)
    return {"messages": [llm_response]}
def create_async_tools_graph(api_key: str, model_name: str, base_url: str):
    com_llm = ChatOpenAI(
        model=model_name,
        temperature=0.0,
        max_retries=2,
        openai_api_key=api_key,
        openai_api_base=base_url,
    )

    # 使用 functools.partial 绑定参数
    _generate_research_topic = functools.partial(generate_research_topic, com_llm=com_llm)
    _chatbox = functools.partial(chatbox, com_llm=com_llm)
    _file_research = functools.partial(
        file_research,
        com_llm=com_llm,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name
    )
    _final_answer = functools.partial(final_answer, com_llm=com_llm)

    # 构建图
    builder = StateGraph(OverallState)

    builder.add_node("generate_research_topic", _generate_research_topic)
    builder.add_node("chatbox", _chatbox)
    builder.add_node("file_research", _file_research)
    builder.add_node("final_answer", _final_answer)

    # 条件边等保持不变
    builder.add_edge(START, "generate_research_topic")

    def tools_condition(state: OverallState):
        search_queries = state.get("search_query")
        if isinstance(search_queries, list) and len(search_queries) > 0:
            last_query = search_queries[-1]
            if isinstance(last_query, str) and last_query.strip() != "":
                return "file_research"
        return "chatbox"

    builder.add_conditional_edges(
        "generate_research_topic",
        tools_condition,
        {
            "file_research": "file_research",
            "chatbox": "chatbox"
        }
    )
    builder.add_edge("file_research", "final_answer")
    builder.add_edge("final_answer", END)
    builder.add_edge("chatbox", END)

    return builder.compile(checkpointer=checkpointer)

# --- 保留用于独立测试的 main 函数 ---
# 主函数
async def main():
    # 创建图实例 (注意：现在需要传参)
    # 为了独立运行，这里还是从环境变量获取
    api_key = os.getenv("OPENAI_API_KEY", "sk-xx")
    model_name = os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-7B-Instruct")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")

    graph = create_async_tools_graph(api_key, model_name, base_url)

    print("欢迎使用检索聊天机器人！输入 'exit' 或 'q' 退出。")
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            config = {"configurable": {"thread_id": "1"}}
            response = await graph.ainvoke({"messages": [HumanMessage(content=user_input)]
                                            }, config)
            ai_message = response["messages"][-1]
            print(f"AI: {ai_message.content}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break

# 运行主函数
if __name__ == "__main__":
    asyncio.run(main())

