import os
import asyncio

from src.filecontentextract import FileContentExtract


async def perform_analysis(researcher, file_paths, research_topic):
    """
    执行文件内容提取和分析，并输出结果。
    """
    all_results = await researcher.async_run(
        file_paths=file_paths,
        research_topic=research_topic
    )

    content = researcher.get_markdown_ref()
    answer = researcher.final_answer(research_topic=research_topic, content=content)
    print("\n【最终答案】\n")
    print(answer)

async def main():
    model_name = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
    api_key = os.getenv("OPENAI_API_KEY", "sk-xxxx")

    while True:
        # 初始化参数
        research_topic = ''
        input_file_paths = ''

        # 获取研究主题
        while not research_topic.strip():
            research_topic = input("\n请输入研究主题（或输入 'exit' 退出）: ").strip()

        if research_topic.lower() == 'exit':
            print("退出程序。")
            break

        # 获取文件路径
        while not input_file_paths.strip():
            input_file_paths = input("请输入查询目录（默认当前目录，或输入 '.'）: ").strip()

        # 处理文件路径
        if input_file_paths in ('.', '') or not input_file_paths:
            file_paths = [os.path.abspath(os.getcwd())]
        else:
            file_paths = [os.path.abspath(input_file_paths.replace('\\', os.sep).replace('/', os.sep))]

        # 创建研究员实例
        researcher = FileContentExtract(
            model=model_name,
            api_key=api_key,
            api_base=base_url,
            name='ResearcherAgent'
        )

        # 执行分析
        await perform_analysis(researcher, file_paths, research_topic)

        # 是否继续
        choice = input("\n是否继续进行下一次分析？(y/n): ").strip().lower()
        if choice not in ('y', 'yes',''):
            print("感谢使用，再见！")
            break


if __name__ == "__main__":
    asyncio.run(main())
