import operator
from typing import Dict, List, Optional, TypedDict, Any
from typing_extensions import Annotated

from langgraph.graph import add_messages
from pydantic.v1 import BaseModel

# ===== 文件抽取返回机构 =====
class FileMatch(BaseModel):
    start_line: int
    end_line: int 
    reasoning: str

# ===== 文件抽取返回机构列表 =====
class FileMatchList(BaseModel):
    args: List[FileMatch]

# ===== 保持与"gemini-fullstack-langgraph-quickstart"项目机构一致 =====
class OverallState(TypedDict):
    messages: Annotated[list, add_messages]
    search_query: Annotated[list, operator.add]
    web_research_result: Annotated[list, operator.add]
    sources_gathered: Annotated[list, operator.add]
    initial_search_query_count: int
    max_research_loops: int
    research_loop_count: int
    reasoning_model: str
