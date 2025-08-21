
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage
from datetime import datetime
import os
import shutil
from shiny import ui
from typing import Dict, List, Optional, Any,Union
import requests
from markitdown import MarkItDown
from urllib.parse import urlparse

import logging
logger = logging.getLogger(__name__)

def get_current_date():
  return datetime.now().strftime("%Y-%m-%d")

def get_research_topic(messages: List[AnyMessage]) -> str:
    """
    Get the research topic from the messages.
    """
    # check if request has a history and combine the messages into a single string
    if len(messages) == 1:
        research_topic = messages[-1].content
    else:
        research_topic = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                research_topic += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                research_topic += f"Assistant: {message.content}\n"
    return research_topic


def resolve_urls(urls_to_resolve: List[Any], id: int) -> Dict[str, str]:
    """
    Create a map of the vertex ai search urls (very long) to a short url with a unique id for each url.
    Ensures each original URL gets a consistent shortened form while maintaining uniqueness.
    """
    prefix = f"https://vertexaisearch.cloud.google.com/id/"
    urls = [site.web.uri for site in urls_to_resolve]

    # Create a dictionary that maps each unique URL to its first occurrence index
    resolved_map = {}
    for idx, url in enumerate(urls):
        if url not in resolved_map:
            resolved_map[url] = f"{prefix}{id}-{idx}"

    return resolved_map


def insert_citation_markers(text, citations_list):
    """
    Inserts citation markers into a text string based on start and end indices.

    Args:
        text (str): The original text string.
        citations_list (list): A list of dictionaries, where each dictionary
                               contains 'start_index', 'end_index', and
                               'segment_string' (the marker to insert).
                               Indices are assumed to be for the original text.

    Returns:
        str: The text with citation markers inserted.
    """
    sorted_citations = sorted(
        citations_list, key=lambda c: (c["end_index"], c["start_index"]), reverse=True
    )

    modified_text = text
    for citation_info in sorted_citations:
        end_idx = citation_info["end_index"]
        marker_to_insert = ""
        for segment in citation_info["segments"]:
            marker_to_insert += f" [{segment['label']}]({segment['short_url']})"

        modified_text = (
            modified_text[:end_idx] + marker_to_insert + modified_text[end_idx:]
        )

    return modified_text


def get_citations(response, resolved_urls_map):
    """
    Extracts and formats citation information from a Gemini model's response.

    This function processes the grounding metadata provided in the response to
    construct a list of citation objects. Each citation object includes the
    start and end indices of the text segment it refers to, and a string
    containing formatted markdown links to the supporting web chunks.

    Args:
        response: The response object from the Gemini model, expected to have
                  a structure including `candidates[0].grounding_metadata`.
                  It also relies on a `resolved_map` being available in its
                  scope to map chunk URIs to resolved URLs.

    Returns:
        list: A list of dictionaries, where each dictionary represents a citation
              and has the following keys:
              - "start_index" (int): The starting character index of the cited
                                     segment in the original text. Defaults to 0
                                     if not specified.
              - "end_index" (int): The character index immediately after the
                                   end of the cited segment (exclusive).
              - "segments" (list[str]): A list of individual markdown-formatted
                                        links for each grounding chunk.
              - "segment_string" (str): A concatenated string of all markdown-
                                        formatted links for the citation.
              Returns an empty list if no valid candidates or grounding supports
              are found, or if essential data is missing.
    """
    citations = []

    # Ensure response and necessary nested structures are present
    if not response or not response.candidates:
        return citations

    candidate = response.candidates[0]
    if (
        not hasattr(candidate, "grounding_metadata")
        or not candidate.grounding_metadata
        or not hasattr(candidate.grounding_metadata, "grounding_supports")
    ):
        return citations

    for support in candidate.grounding_metadata.grounding_supports:
        citation = {}

        # Ensure segment information is present
        if not hasattr(support, "segment") or support.segment is None:
            continue  # Skip this support if segment info is missing

        start_index = (
            support.segment.start_index
            if support.segment.start_index is not None
            else 0
        )

        # Ensure end_index is present to form a valid segment
        if support.segment.end_index is None:
            continue  # Skip if end_index is missing, as it's crucial

        # Add 1 to end_index to make it an exclusive end for slicing/range purposes
        # (assuming the API provides an inclusive end_index)
        citation["start_index"] = start_index
        citation["end_index"] = support.segment.end_index

        citation["segments"] = []
        if (
            hasattr(support, "grounding_chunk_indices")
            and support.grounding_chunk_indices
        ):
            for ind in support.grounding_chunk_indices:
                try:
                    chunk = candidate.grounding_metadata.grounding_chunks[ind]
                    resolved_url = resolved_urls_map.get(chunk.web.uri, None)
                    citation["segments"].append(
                        {
                            "label": chunk.web.title.split(".")[:-1][0],
                            "short_url": resolved_url,
                            "value": chunk.web.uri,
                        }
                    )
                except (IndexError, AttributeError, NameError):
                    # Handle cases where chunk, web, uri, or resolved_map might be problematic
                    # For simplicity, we'll just skip adding this particular segment link
                    # In a production system, you might want to log this.
                    pass
        citations.append(citation)
    return citations


def clear_docs_folder(docs_path:str):

    if os.path.exists(docs_path):
        # 如果存在，删除整个目录及其内容
        try:
            shutil.rmtree(docs_path)
            logger.info("docs 目录已删除")
        except Exception as e:
            logger.error("删除 docs 目录失败：%s", str(e))
            return False

    # 重新创建空的 docs 目录
    try:
        os.makedirs(docs_path)
        logger.info("docs 目录已重新创建")
        return True
    except Exception as e:
        logger.error("创建 docs 目录失败：%s", str(e))
        return False

def webfetch(
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

def cpoy_directory(src_dir: str, target_dir: str):

    # 获取用户选择的目录
    selected_dir = src_dir.strip()

    # 创建目标目录
    if not os.path.exists(selected_dir):
        logger.warning("目标目录不存在")
        return []

    all_files = []
    # 当输入是单个文件路径
    if os.path.isfile(selected_dir):

        src_file = selected_dir
        dest_file = os.path.join(target_dir, os.path.basename(selected_dir))

        try:
            shutil.copy2(src_file, dest_file)  # 拷贝并保留元数据
            all_files.append(dest_file)
            logger.info("已复制：%s → %s", src_file, dest_file)
            ui.notification_show(f"✅ 已复制：{src_file} → {dest_file}", type="message", duration=10)

        except Exception as e:
            logger.error("复制失败：%s，错误：%s", src_file, str(e))
            ui.notification_show(f"❌ 复制失败：{src_file}，错误：{str(e)}", type="message", duration=10)

    # 当输入是目录路径
    else:
        for root, _, files in os.walk(selected_dir):
            rel_path = os.path.relpath(root, selected_dir)
            dest_subdir = os.path.join(target_dir, rel_path)
            os.makedirs(dest_subdir, exist_ok=True)

            for f in files:
                src_file = os.path.join(root, f)
                dest_file = os.path.join(dest_subdir, f)

                try:
                    shutil.copy2(src_file, dest_file)  # 拷贝并保留元数据
                    all_files.append(dest_file)
                    logger.info("已复制：%s → %s", src_file, dest_file)
                    ui.notification_show(f"✅ 已复制：{src_file} → {dest_file}", type="message", duration=10)

                except Exception as e:
                    logger.error("复制失败：%s，错误：%s", src_file, str(e))
                    ui.notification_show(f"❌ 复制失败：{src_file}，错误：{str(e)}", type="message", duration=10)
   
    ui.notification_show("✅ 目录文件拷贝完成", type="message", duration=10)

    return all_files
