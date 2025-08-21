import os
import asyncio
import mimetypes
import hashlib
from typing import Dict, List, Optional, TypedDict, Any,Union
from pathlib import Path
from functools import partial
import logging

import requests
from markitdown import MarkItDown
from urllib.parse import urlparse

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .models import FileMatchList, OverallState
from .directorytreegenerator import DirectoryTreeGenerator
from .prompts_zh import file_extract_instructions,final_answer_instructions

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
        self.config = {"configurable": {"thread_id": "chatbot_agent"}}

        #graph.stream({"messages": [{"role": "user", "content": user_input}]}, config)
        # 构建 prompt 模板
        self.extract_prompt = ChatPromptTemplate.from_messages([
            ("system", file_extract_instructions),
            ("human", "[ ## Context ## ]\n行号:内容\n---{file_content}"),
        ])

        # 构建链式调用
        self.extract_chain = self.extract_prompt | self.llm.with_structured_output(FileMatchList, method="function_calling")

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
        #print("result:", result)
        if result is None:
            # 可以记录日志、抛出异常，或返回空 matches
            logger.warning("content_extract returned None")
            matches = []
        else:
            matches = []
            for item in result.args:
                matches.append({
                    "start_line": item.start_line,
                    "end_line": item.end_line,
                    "reasoning": item.reasoning
                })

        return matches

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

        #print("Assistant:", result["messages"][-1].content)
        return result.content

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
            logger.warning("无效路径: %s", path)

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
<hr>
<strong>来源[{index}]：</strong> 
<code>{filename}</code>，第 <strong>{start_line}</strong> 至 <strong>{end_line}</strong> 行<br>

<strong>匹配原因：</strong>
{reason}

<strong>匹配内容：</strong>
```text

{content}

```
</blockquote>
<!-- 第 {index} 个引用结束 -->"""

        return template

    def read_file(self, path: str) -> Optional[Dict]:
        """
        读取指定路径的文件内容，并添加行号前缀。
        """
        if not os.path.exists(path):
            logger.warning("文件路径不存在: %s", path)
            return None

        is_file = os.path.isfile(path)
        if not is_file:
            logger.warning("路径不是一个文件")
            return None

        file_name = os.path.basename(path)
        file_size = os.path.getsize(path)

        mime_type, _ = mimetypes.guess_type(path)
        file_type = mime_type or os.path.splitext(path)[1][1:].lower() or "unknown"

        try:
            with open(path, 'r', encoding='utf-8') as f:
                context = f.read()
        except Exception as e:
            logger.error("无法读取文件内容: %s", e)
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
        logger.info("Scanning 执行完成: %s", file_path)

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

    def webfetch(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        allow_redirects: bool = True,
        proxy: Optional[str] = None,
        cookies: Optional[Union[Dict[str, str], requests.cookies.RequestsCookieJar]] = None,
        verify_ssl: bool = True,
    ) -> Optional[str]:
        """
        通用网页抓取并转换为 Markdown 的函数。

        Args:
            url (str): 目标网页 URL。
            headers (dict, optional): 自定义请求头。默认使用常见浏览器头。
            timeout (int): 请求超时时间（秒）。
            allow_redirects (bool): 是否允许重定向。
            proxy (str, optional): 代理地址，如 "http://127.0.0.1:8080"。
            cookies (dict or RequestsCookieJar, optional): 附加 cookies。
            verify_ssl (bool): 是否验证 SSL 证书。

        Returns:
            str or None: 返回转换后的 Markdown 文本，失败返回 None。
        """
        # 默认请求头（模拟现代浏览器）
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }

        # 合并用户自定义 headers 到默认 headers（用户优先）
        final_headers = default_headers.copy()
        if headers:
            final_headers.update(headers)

        # 构建 requests kwargs
        requests_kwargs = {
            "headers": final_headers,
            "timeout": timeout,
            "allow_redirects": allow_redirects,
            "verify": verify_ssl,
        }

        if proxy:
            requests_kwargs["proxies"] = {
                "http": proxy,
                "https": proxy,
            }

        if cookies:
            requests_kwargs["cookies"] = cookies

        try:
            # 验证 URL 格式
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError(f"Invalid URL: {url}")

            # 创建 MarkItDown 实例
            md_converter = MarkItDown(requests_kwargs=requests_kwargs)

            # 执行转换
            result = md_converter.convert_uri(url)

            return result.markdown

        except requests.exceptions.SSLError as e:
            logger.error("SSL 错误: %s", e)
        except requests.exceptions.Timeout:
            logger.error("请求超时: %s (>%ds)", url, timeout)
        except requests.exceptions.TooManyRedirects:
            logger.error("重定向过多: %s", url)
        except requests.exceptions.RequestException as e:
            logger.error("网络请求错误: %s", e)
        except Exception as e:
            logger.error("未知错误: %s", e)

        return None

    def url_scanning(self, url: str, research_topic: str) -> Optional[OverallState]:
        """
        分析单个URL并返回结构化结果。
        """
        # 获取网页内容
        content = self.webfetch(url=url)
        if not content:
            logger.warning("无法获取URL内容: %s", url)
            return None

        try:
            # 构造查询上下文
            context = (
                f"[ ## 当前访问URL ## ]\n{url}\n\n"
                f"[ ## context ## ]\n行号:内容---\n{self._add_line_numbers(content)}"
            )

            # 执行 AI 查询
            matches = self.content_extract(file_content=context, research_topic=research_topic)

            # 组装 sources_gathered
            sources_gathered = []
            for match in matches:
                sources_gathered.append({
                    "file_path": url,
                    "start_line": match["start_line"],
                    "end_line": match["end_line"],
                    "reasoning": match["reasoning"],
                    "relevant_content": self._get_lines_by_range(
                        content, match["start_line"], match["end_line"]
                    )
                })

            # 收集相关文本内容
            web_research_result = [match["reasoning"] for match in matches]
            logger.info("URL processing completed: %s", url)

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
        except Exception as e:
            logger.error("处理URL内容时出错: %s, 错误: %s", url, e)
            return None

    def run(self, file_paths: List[str], research_topic:str)->List[OverallState]:
        """
        批量运行文件分析，支持多个文件。
        """
        results = []
        for file_path in file_paths:

            #参数是文件
            if os.path.isfile(file_path):
                logger.info("Scanning the file: %s", file_path)
                result = self.scanning(file_path, None, research_topic)
                results.append(result)

            #参数是目录
            elif os.path.isdir(file_path):
                logger.info("Scanning the directory: %s", file_path)
                # 获取目录树
                tree_str = DirectoryTreeGenerator(file_path).generate_tree(
                    include_hidden=False,
                    include_extensions=[".py", ".md", ".txt"]
                )
                
                # 获取目录列表
                file_list = self._filelist(file_path)
                for _file_paths in file_list:
                    logger.info("Scanning the file: %s", _file_paths)
                    result = self.scanning( _file_paths, tree_str, research_topic)
                    results.append(result)
            else:
                logger.warning("找不到文件或目录：%s", file_path)

        self.last_results = results
        return results

    async def async_run(self, file_paths: List[str], urls: List[str], research_topic:str  )->List[OverallState]:
        """
        异步批量运行文件分析，支持多个文件。
        """
        results = []
        loop = asyncio.get_event_loop()

        # 文件类型
        for file_path in file_paths:
            if os.path.isfile(file_path):
                logger.info("Scanning the file: %s", file_path)
                # 在线程池中运行阻塞函数
                result = await loop.run_in_executor(None, self.scanning, file_path, None, research_topic)
                results.append(result)

            elif os.path.isdir(file_path):
                logger.info("Scanning the directory: %s", file_path)

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
                    logger.info("Scanning the file: %s", _file_path)
                    task = loop.run_in_executor(None, self.scanning, _file_path, tree_str, research_topic)
                    tasks.append(task)

                # 并发执行并收集结果
                batch_results = await asyncio.gather(*tasks)
                results.extend(batch_results)

            else:
                logger.warning("找不到文件或目录：%s", file_path)

        # 处理 URLs（仅当urls不为空时）
        if urls is not None and len(urls) > 0:  # 更准确地判断urls是否为None或空
            for url in urls:
                logger.info("Processing URL: %s", url)
                result = await loop.run_in_executor(None, self.url_scanning, url, research_topic)
                if result:
                    results.append(result)

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
                        
                        if source['relevant_content'] and source['relevant_content'].strip():
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
                        logger.error("缺少必要字段: %s，source 数据：%s", e, source)
                    except Exception as ex:
                        logger.error("处理 source 时发生错误: %s", ex)

        full_markdown = "\n\n".join(references)
        #print(full_markdown)
        return full_markdown
