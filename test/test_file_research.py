#!/usr/bin/env python3
"""
测试 podcast_llm/writer.py 的 file_research 函数
"""

import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from podcast_llm.writer import file_research


def test_file_research():
    """测试 file_research 函数"""
    # 配置参数（请根据实际情况修改）
    api_key = "your_api_key_here"  # 替换为实际的 API 密钥
    base_url = "your_base_url_here"  # 替换为实际的 API 基础 URL
    model_name = "your_model_name_here"  # 替换为实际的模型名称
    research_topic = "人工智能的发展历程"
    file_path = "./README.md"  # 使用项目中的一个文件作为测试
    urls = ["https://www.wikipedia.org/"]  # 示例 URL

    try:
        print("开始测试 file_research 函数...")
        print(f"研究主题: {research_topic}")
        print(f"文件路径: {file_path}")
        print(f"URL 列表: {urls}")

        # 调用函数
        result = file_research(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            research_topic=research_topic,
            file_path=file_path,
            urls=urls
        )

        print("函数调用成功！")
        print("结果预览:")
        print(result[:200] + "..." if len(result) > 200 else result)
        return True

    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_file_research()
    if success:
        print("\n测试通过!")
    else:
        print("\n测试失败!")
        sys.exit(1)