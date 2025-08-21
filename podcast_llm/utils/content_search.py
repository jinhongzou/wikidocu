"""
Utilities for content research

"""

import os
import logging
from typing import Any, Callable
from pathlib import Path
from src.filecontentextract import FileContentExtract, FileMatchList

logger = logging.getLogger(__name__)

def content_search(api_key=os.getenv("OPENAI_API_KEY", "sk-xxx"),
                  base_url=os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1"),
                  model_name=os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
                  research_topic=None, 
                  context=None
                  ) -> str:

    researcher = FileContentExtract(
        model=model_name,
        api_key=api_key,
        api_base=base_url,
        name='ResearcherAgent'
    )

    result = researcher.content_extract(
        file_content=context,
        research_topic=research_topic
    )


    response_matches: FileMatchList = result

    # 组装 sources_gathered
    sources_gathered = []
    for match in response_matches:
        sources_gathered.append({
            "file_path": '',
            "start_line": match["start_line"],
            "end_line": match["end_line"],
            "reasoning": match["reasoning"],
            "relevant_content": researcher._get_lines_by_range(
                context, match["start_line"], match["end_line"]
            )
        })

    # 收集相关文本内容
    web_research_result = [match["reasoning"] for match in response_matches]

    all_results = {
        "sources_gathered": sources_gathered,
        "search_query": [research_topic],
        "web_research_result": web_research_result,
        "messages": [],
        "initial_search_query_count": 0,
        "max_research_loops": 0,
        "research_loop_count": 0,
        "reasoning_model": '',
    }

    # 提取内容，并格式化
    formatted_contents = [
        f"<参考内容>：{item['relevant_content']}</参考内容>"
        for item in all_results['sources_gathered']
        if item.get('relevant_content') and item['relevant_content'].strip()
    ]    
    #logger.info(f"{len(all_results['sources_gathered'])} 条内容被提取.")

    # 用两个换行符连接，使每条引用之间有空行
    return "\n\n".join(formatted_contents)
