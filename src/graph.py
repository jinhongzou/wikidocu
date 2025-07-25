
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

model_name = os.getenv("MODEL_NAME", "your-model-name")
model_name_answer = os.getenv("MODEL_NAME_QWEN3", "your-model-name")
base_url = os.getenv("OPENAI_BASE_URL", "your-base-url")
api_key = os.getenv("OPENAI_API_KEY", "your-api-key")

# 普通 LLM
com_llm = ChatOpenAI(
    model=model_name,
    temperature=0.0,
    max_retries=2,
    openai_api_key=api_key,
    openai_api_base=base_url,
)

# 高级 LLM
adn_llm = ChatOpenAI(
    model=model_name_answer,
    temperature=0.0,
    max_retries=2,
    openai_api_key=api_key,
    openai_api_base=base_url,
)

# 创建 checkpointer
checkpointer = MemorySaver()

# Nodes
def generate_research_topic(state: OverallState) -> QueryGenerationState:
    """LangGraph node that generates search queries based on the User's question.

    Uses Gemini 2.0 Flash to create an optimized search queries for web research based on
    the User's question.

    Args:
        state: Current graph state containing the User's question
        config: Configuration for the runnable, including LLM provider settings

    Returns:
        Dictionary with state update, including search_query key containing the generated queries
    """
    # check for custom initial search query count
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = 3

    structured_llm = com_llm.with_structured_output(SearchQueryList)

    # Format the prompt
    current_date = get_current_date()
    #question=state["messages"][-1].content
    chat_messages=state["messages"]
    question=state["messages"][-1].content

    formatted_prompt = general_doc_retrieval_prompt.format(
        current_date=current_date,
        research_topic=chat_messages,
        number_queries=state["initial_search_query_count"],
    )
    # Generate the search queries
    result = structured_llm.invoke(formatted_prompt)
    
    search_queries = result.query

    # 判断是否需要检索
    if isinstance(search_queries, list) and len(search_queries) > 0 and search_queries[-1].strip() != "":
        search_query= f"问题:{question}。 关键点：" + ', '.join(search_queries)

        ui_detail_output_handler._turns=ui_detail_output_handler._turns+1
        ui_detail_output_handler.write_content(f"---\n### 第 [{ui_detail_output_handler._turns}] 轮检索\n### [输入问题]:\n{question}\n### [增强检索]:\n{search_query}\n")

        return {"search_query": [search_query]}

    else:
         # 推荐写法
        return {"search_query": []}

#toolnode
async def chatbox(state: OverallState):
    """处理用户查询，决定是否需要调用工具"""
    # 获取最新的用户消息
    #print(state["messages"])
    #user_message = state["messages"][-1].content

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

#toolnode
async def file_research(state: OverallState) -> OverallState:
    """
    使用本地文件内容检索机制，根据当前状态中的 search_query 执行文件内容搜索。
    该工具适用于在知识库中查找与查询主题相关的文档内容。

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
        'search_query':[research_topic],
        'web_research_result':[content_md]
        }

#toolnode
async def final_answer(state: OverallState):
    """处理用户查询，决定是否需要调用工具"""
    #user_message = state["messages"][-1].content
    #context = state.get("web_research_result", "") 
    #research_topic = state.get("search_query", "")
    if state.get("search_query"):
        research_topic= state["search_query"][-1]

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

    return {"messages": llm_response}

def create_async_tools_graph():
    """创建使用异步工具的状态图"""
    builder = StateGraph(OverallState)

    # 添加节点
    builder.add_node("generate_research_topic", generate_research_topic)
    builder.add_node("chatbox", chatbox)
    builder.add_node("file_research", file_research)
    builder.add_node("final_answer", final_answer)
    #builder.add_node("tools", ToolNode(tools=tools))

    # 添加边
    builder.add_edge(START, "generate_research_topic")

    def tools_condition(state: OverallState):
        search_queries = state.get("search_query")
        #print(f"---\n{search_queries},{len(search_queries)}")

        if isinstance(search_queries, list) and len(search_queries) > 0:
            # 取最后一个查询项
            last_query = search_queries[-1]
            # 判断是否是字符串，且非空或空白
            if isinstance(last_query, str) and last_query.strip() != "":
                return "file_research"

        return "chatbox"

    # 添加条件边，使用自定义路由函数
    builder.add_conditional_edges(
        "generate_research_topic",
        tools_condition,  #这个函数应该返回 'tools'、'file_research' 或 'final_answer'
        {
            #"tools": "tools",           # 假设有这个节点
            "file_research": "file_research",
            "chatbox": "chatbox"                     # 新增的分支
        }
    )
    builder.add_edge("file_research", "final_answer")
    builder.add_edge("final_answer", END)
    builder.add_edge("chatbox", END)

    # 编译图，并传入 checkpointer
    return builder.compile(checkpointer=checkpointer)

# 主函数
async def main():
    # 创建图实例
    graph = create_async_tools_graph()

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
            #print(f": {response}")
            ai_message = response["messages"][-1]
            print(f"AI: {ai_message.content}")

        except KeyboardInterrupt:
            print("\nExiting...")
            break

# 运行主函数
if __name__ == "__main__":
    asyncio.run(main())

