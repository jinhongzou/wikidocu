import os
import asyncio
import mimetypes
import operator
import hashlib
from typing import Dict, List, Optional, TypedDict, Any
from pathlib import Path
from functools import partial

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .models import FileMatchList, OverallState
from .directorytreegenerator import DirectoryTreeGenerator
from .prompts_zh import file_extract_instructions,final_answer_instructions


import logging

# 初始化 logger
logger = logging.getLogger(__name__)

class FileContentExtract:
    def __init__(
        self,
        model: str,
        api_key: str ,
        api_base: str,
        name: str='FileContentExtract'
    ) -> None:
        # 初始化模型
        self.llm = ChatOpenAI(
            model=model,
            temperature=0.0,
            max_retries=2,
            openai_api_key=api_key,
            openai_api_base=api_base,
        )
        self.name = name

        # 构建 prompt 模板
        self.extract_prompt = ChatPromptTemplate.from_messages([
            ("system", file_extract_instructions),
            ("human", "[ ## Context ## ]\n行号:内容\n---{file_content}"),
        ])

        # 构建链式调用
        self.extract_chain = self.extract_prompt | self.llm.with_structured_output(FileMatchList, method="function_calling")


    def final_answer(self,  research_topic: str, content: str) -> str:
        """
        基于提供的内容分析用户的查询。

        参数:
            research_topic (str): 用户的问题或研究主题
            content (str): 提供给模型参考的文件内容或检索内容

        返回:
            str: 模型根据内容对用户问题的回答
        """

        # 构建 prompt 模板
        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", final_answer_instructions),
            ("human", "[ ## 上下文 ## ]\n{content}"),
        ])

        # 构建链并调用
        answer_chain = answer_prompt | self.llm

        # 调用链并传入参数
        result = answer_chain.invoke({
            "research_topic": research_topic,
            "content": content
        })
        
        print("[final_answer]执行完成.")
        return result.content

    def content_extract(self, 
                        file_content: str,
                        research_topic: str ) -> FileMatchList:
        """
        执行分析并返回结构化结果
        :param file_content: 文件内容，带行号格式如 '1: 内容'
        :param research_topic: 研究主题
        :return: 列表，每个元素包含 start_line, end_line, reasoning
        """
        result = self.extract_chain.invoke({
            "research_topic": research_topic,
            "file_content": file_content
        })

        matches = []
        for item in result.args:
            matches.append({
                "start_line": item.start_line,
                "end_line": item.end_line,
                "reasoning": item.reasoning
            })
        return matches

    def _filelist(self, path: str, include_hidden: bool = False, include_extensions: Optional[List[str]] = None) -> List[str]:
        """
        获取指定路径下所有文件的完整路径列表。
        支持过滤隐藏文件和指定扩展名。
        :param path: 文件或目录路径
        :param include_hidden: 是否包含隐藏文件
        :param include_extensions: 允许的文件扩展名列表（如[".py", ".md"]），None表示不过滤
        :return: 文件路径列表
        """
        file_paths = []

        if os.path.isfile(path):
            # 如果是单个文件，判断是否符合过滤条件
            if not include_hidden and os.path.basename(path).startswith('.'):
                return []
            if include_extensions is not None and os.path.splitext(path)[1] not in include_extensions:
                return []
            file_paths.append(path)
        elif os.path.isdir(path):
            # 如果是目录，遍历并添加每个文件路径
            for root, dirs, files in os.walk(path):
                # 过滤隐藏目录
                if not include_hidden:
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                for file in files:
                    if not include_hidden and file.startswith('.'):
                        continue
                    if include_extensions is not None and os.path.splitext(file)[1] not in include_extensions:
                        continue
                    file_path = os.path.join(root, file)
                    file_paths.append(file_path)
        else:
            print("无效路径:", path)

        return file_paths

    # 构造查询上下文，为每一行内容添加行号前缀
    def _add_line_numbers(self, text: str) -> str:
        lines = text.splitlines()
        return "\n".join(f"{idx + 1}: {line}" for idx, line in enumerate(lines))

    def _get_lines_by_range(self, text: str, start_line: int, end_line: int) -> str:
        """
        根据指定的起始和结束行号，返回对应的原始文本内容（不带行号，行号从1开始）。
        """
        lines = text.splitlines()
        # 行号从1开始，Python索引从0开始
        selected = lines[start_line - 1:end_line]
        return "\n".join(selected)
    
    def _generate_markdown_ref(self, index, filename, start_line, end_line, reason, content):
        template = f"""<!-- 第 {index} 个引用开始 -->
<blockquote>
<small>来源【{index}】：<code>{filename}</code>，第 <strong>{start_line}</strong> 至 <strong>{end_line}</strong> 行</small><br>

<em>匹配原因：{reason}</em>

<strong>匹配内容：</strong>

{content}

</blockquote>
<!-- 第 {index} 个引用结束 -->"""

        return template

    def read_file(self, path: str) -> Optional[Dict]:
        """
        读取指定路径的文件内容，并添加行号前缀。
        """
        if not os.path.exists(path):
            print(f"文件路径不存在: {path}")
            return None

        is_file = os.path.isfile(path)
        if not is_file:
            print("路径不是一个文件")
            return None

        file_name = os.path.basename(path)
        file_size = os.path.getsize(path)

        mime_type, _ = mimetypes.guess_type(path)
        file_type = mime_type or os.path.splitext(path)[1][1:].lower() or "unknown"

        try:
            with open(path, 'r', encoding='utf-8') as f:
                context = f.read()
        except Exception as e:
            print(f"无法读取文件内容: {e}")
            return None

        return {
            "file_path": path,
            "file_hash": hashlib.md5(path.encode('utf-8')).hexdigest(),
            "context": context,
            "file_name": file_name,
            "file_type": file_type,
            "file_size": file_size,
        }


    def scanning(self, file_path: str, tree_str: str = None, research_topic: str = None) -> OverallState:
        """
        分析单个文件并返回结构化结果。
        """

        # 判断文件是否存在
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 读取文件内容
        file_result = self.read_file(file_path)
        if not file_result or "context" not in file_result:
            raise ValueError(f"无法读取文件内容: {file_path}")

        # 构造查询上下文
        if not tree_str:
            context = (
                f"[ ## 当前访问文件位置 ## ]\n{file_path}\n\n"
                f"[ ## context ## ]\n行号:内容---\n{self._add_line_numbers(file_result['context'])}"
            )
        else:
            context = (
                f"[ ## 目录树 ## ]\n{tree_str}\n\n"
                f"[ ## 当前访问文件位置 ## ]\n{file_path}\n\n"
                f"[ ## context ## ]\n行号:内容---\n{self._add_line_numbers(file_result['context'])}"
            )

        # 执行 AI 查询
        result = self.content_extract(file_content = context,
                                      research_topic =research_topic )
        
        response_matches: FileMatchList = result

        # 组装 sources_gathered
        sources_gathered = []
        for match in response_matches:
            sources_gathered.append({
                "file_path": file_path,
                "start_line": match["start_line"],
                "end_line": match["end_line"],
                "reasoning": match["reasoning"],
                "relevant_content": self._get_lines_by_range(
                    file_result["context"], match["start_line"], match["end_line"]
                )
            })

        # 收集相关文本内容
        web_research_result = [match["reasoning"] for match in response_matches]
        print("[scanning]执行完成.")

        return {
            "sources_gathered": sources_gathered,
            "search_query": [context],
            "web_research_result": web_research_result,
            "messages": [],
            "initial_search_query_count": 0,
            "max_research_loops": 0,
            "research_loop_count": 0,
            "reasoning_model": self.name,
        }

    def run(self, file_paths: List[str], research_topic:str)->List[OverallState]:
        """
        批量运行文件分析，支持多个文件。
        """
        results = []
        for file_path in file_paths:

            #参数是文件
            if os.path.isfile(file_path):
                print(f"Scanning the file: {file_path}")
                result = self.scanning(file_path, None, research_topic)
                results.append(result)

            #参数是目录
            elif os.path.isdir(file_path):
                print(f"Scanning the directory: {file_path}")
                # 获取目录树
                tree_str = DirectoryTreeGenerator(file_path).generate_tree(
                    include_hidden=False,
                    include_extensions=[".py", ".md", ".txt"]
                )

                # 获取目录列表
                file_list = self._filelist(file_path)
                for _file_paths in file_list:
                    print(f"Scanning the file: {_file_paths}")
                    result = self.scanning( _file_paths, tree_str, research_topic)
                    results.append(result)
            else:
                print(f"\n 找不到文件或目录：{file_path}")
        
        self.last_results = results
        return results

    async def async_run(self, file_paths: List[str], research_topic:str)->List[OverallState]:
        """
        异步批量运行文件分析，支持多个文件。
        """
        results = []
        loop = asyncio.get_event_loop()

        for file_path in file_paths:
            if os.path.isfile(file_path):
                print(f"Scanning the file: {file_path}")
                # 在线程池中运行阻塞函数
                result = await loop.run_in_executor(None, self.scanning, file_path, None, research_topic)
                results.append(result)

            elif os.path.isdir(file_path):
                print(f"Scanning the directory: {file_path}")

                # 构造目录树（假设 DirectoryTreeGenerator.generate_tree() 是同步函数）
                tree_str = await loop.run_in_executor(
                    None,
                    partial(DirectoryTreeGenerator(file_path).generate_tree, include_hidden=False, include_extensions=[".py", ".md", ".txt"])
                )

                # 获取文件列表（假设 _filelist 是同步函数）
                file_list = await loop.run_in_executor(None, self._filelist, file_path)

                # 创建所有文件扫描任务
                tasks = []
                for _file_path in file_list:
                    print(f"Scanning the file: {_file_path}")
                    task = loop.run_in_executor(None, self.scanning, _file_path, tree_str, research_topic)
                    tasks.append(task)

                # 并发执行并收集结果
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)

            else:
                print(f"\n找不到文件或目录：{file_path}")

        self.last_results = results
        return results

    def get_markdown_ref(self):
        # ===== 输出结果 ===== 
        references = []# 用于保存所有生成的引用块
        if hasattr(self, "last_results") and self.last_results is not None:
            for result_idx, result in enumerate(self.last_results):
                # 获取当前结果中的引用信息列表
                sources = result.get("sources_gathered", [])

                if not sources:
                    continue  # 跳过没有 source 的结果

                for source_idx, source in enumerate(sources):
                    try:
                        # 提取 source 中的关键字段
                        file_path = source['file_path']
                        start_line = source['start_line']
                        end_line = source['end_line']
                        reasoning = source['reasoning']
                        relevant_content = source['relevant_content']
                        
                        # 生成对应的 Markdown 引用块
                        ref_block = self._generate_markdown_ref(
                            index=len(references) + 1,  # 自动递增索引，避免依赖外部 loop 变量
                            filename=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            reason=reasoning,
                            content=relevant_content
                        )
                        
                        references.append(ref_block)

                    except KeyError as e:
                        print(f"缺少必要字段: {e}，source 数据：{source}")
                    except Exception as ex:
                        print(f"处理 source 时发生错误: {ex}")

        full_markdown = "\n\n".join(references)
        #print(full_markdown)
        return full_markdown
