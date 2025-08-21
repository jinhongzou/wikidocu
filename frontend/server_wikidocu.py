import os
from dotenv import load_dotenv
from shiny import App, ui, render, reactive
import os
import random
import datetime
from langchain_core.messages import BaseMessage, HumanMessage
import time  # 同步延迟使用
import logging

# 加载 .env 文件
load_dotenv()

logger = logging.getLogger(__name__)


from frontend.navset_builder import NavsetUIBuilder
from frontend.components import create_auto_scroll_div
from frontend.navset_configs import navset_configs
from frontend.utils_wikidocu import generate_full_report, show_api_config_modal, custom_research_body
from src.func_utils import cpoy_directory,webfetch,clear_docs_folder
from src.graph import create_async_tools_graph

from config.global_vars import WIKIDOCU_QA_DIR

builder = NavsetUIBuilder(navset_configs)

# ========== Server Logic ==========
# 初始化时从环境变量获取默认值
api_key = os.getenv("OPENAI_API_KEY", "sk-xxx")
model_name = os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-7B-Instruct")
#model_name_answer= os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-7B-Instruct")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")

def wikidocu_server(input, output,  session):
    g_value_main_output = reactive.Value("")
    g_value_detail_output = reactive.Value("")
    dynamic_ui_content = reactive.Value(ui.TagList())
    g_openai_config=reactive.Value({"model_name": model_name, "base_url": base_url, "api_key": api_key})
    g_sdata = reactive.Value({"paths": WIKIDOCU_QA_DIR, "urls": ""})

    # 显示欢迎模态框
    m = ui.modal(
        ui.markdown(f"""
### 欢迎使用 **WikiDocu** —— 多文档智能问答系统

你可以：

- 📚 **跨文档智能问答**：在多个文档之间建立关联，实现知识的跨文档检索与精准问答，支持复杂场景下的信息整合。
- 🧩 **深度知识理解**：融合代码理解与技术文档生成能力，可深入解析结构化内容（如代码仓库），实现从代码到文档的自动推理与解释。
- 🧠 **上下文感知交互**：支持基于上下文的多轮对话理解，智能定位相关内容，提升检索效率与准确性。
- 🛠 **无需索引构建**：无需预处理构建向量库或索引，直接利用大模型理解内容，部署更轻量，响应更迅速。

请将需要分析的文档放入目录 **`{WIKIDOCU_QA_DIR}`**，然后输入你的问题，点击 **检索**，即可开启高效、智能的知识探索之旅。

⚠️ 注：分析基于当前输入的数据文件和模型理解能力，仅供参考。
"""),
        title="欢迎使用 WikiDocu",
        easy_close=False,
        footer=None
    )
    # 显示模态框
    ui.modal_show(m)
    time.sleep(3)
    ui.modal_remove()

    # 动态生成对话tab
    @output
    @render.ui
    def dynamic_content():

        main_content = g_value_main_output.get()
        detail_content = g_value_detail_output.get()

        if main_content == "":
            return 
    
        if detail_content.strip() == "":
            detail_content='未检索到内容'

        navset_types = list(navset_configs.keys())
        selected_type = random.choice(navset_types)

        new_content = ui.TagList(
            builder.create_navset_ui_from_context(selected_type,
                                                  ui.markdown(main_content),
                                                  ui.markdown(detail_content)
                                                  ),
        )
        current_content = dynamic_ui_content.get()
        current_content.append(new_content)
        dynamic_ui_content.set(current_content)

        return create_auto_scroll_div(dynamic_ui_content.get())

    # 处理“检索”按钮点击前的加载提示和按钮禁用
    @reactive.effect
    @reactive.event(input.custom_send)
    async def handle_custom_send_waiting_notion():
        research_topic = input.custom_message().strip()
        # 清空输入框
        ui.update_text_area(  
            id="custom_message",  
            value=""  
        )
        if not research_topic:
            ui.notification_show("⚠️ 请先输入研究主题。", type="error", duration=10)
            return

        # 显示加载提示 + 失效按键
        ui.notification_show("⏳ 正在分析，请稍候...", type="message", duration=10)
        ui.update_action_button("custom_send", disabled=True)

    # 处理“检索”按钮点击事件，执行核心逻辑
    @reactive.effect
    @reactive.event(input.custom_send)
    async def handle_custom_send():
        research_topic = input.custom_message().strip()
        # 再次清空输入框（以防等待提示逻辑未触发）
        ui.update_text_area(  
            id="custom_message",  
            value=""  
        )
        input_path = WIKIDOCU_QA_DIR

        if not research_topic:
            ui.update_action_button("custom_send", disabled=False)
            return

        # 1. 获取用户配置或使用默认值
        config=g_openai_config.get()
        user_api_key = config.get("api_key")
        user_model_name =  config.get("model_name")
        user_base_url = config.get("base_url")
        #print("config:",    config)

        # 2. 根据用户配置动态创建 graph 实例
        try:
            # 将用户配置传递给 graph 创建函数
            graph = create_async_tools_graph(
                api_key=user_api_key,
                model_name=user_model_name,
                base_url=user_base_url
            )
        except Exception as e:
            ui.notification_show(f"❌ 创建分析器实例失败: {str(e)}", type="error", duration=10)
            g_value_main_output.set("⚠️ 创建分析器实例失败，请检查配置。")
            ui.update_action_button("custom_send", disabled=False)
            return

        config = {"configurable": {"thread_id": "1"}}

        # 3. 准备文件路径
        if not input_path or input_path == '.':
            file_paths = [os.path.abspath(os.getcwd())]
        else:
            file_paths = [os.path.abspath(input_path.replace('\\', os.sep).replace('/', os.sep))]

        # 4. 执行分析
        try:
            response = await graph.ainvoke({"messages": [HumanMessage(content=research_topic)]
                                            }, config)
            
            logger.info("分析执行完成。")

            if response.get("messages"):
                answer_resp = response["messages"][-1].content
            else:
                answer_resp = "未生成答案。"

            if response.get("web_research_result"):
                retrieve_resp = response["web_research_result"][-1]
            else:
                retrieve_resp='未检索到内容'

            timestamp = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

            if not answer_resp.strip():
                full_report = "⚠️ 没有获取到有效的分析结果，请检查输入数据或稍后重试。"
            else:
                full_report = generate_full_report(research_topic, answer_resp, file_paths, timestamp)

            g_value_main_output.set(full_report)
            g_value_detail_output.set(retrieve_resp)

        except Exception as e:
            ui.notification_show(f"❌ 分析过程中发生错误：{str(e)}", type="error", duration=10 )
            g_value_main_output.set("⚠️ 分析过程中发生错误，请重试。")
        finally:
            # 无论成功与否，都启用按钮
            ui.update_action_button("custom_send", disabled=False)

    # 当用户点击“⚙️ 配置”按钮时，显示配置模态框
    @reactive.effect
    @reactive.event(input.open_config)
    def _():
        openai_config=g_openai_config.get()
        sdata=g_sdata.get()
        show_api_config_modal(input, output, session, openai_config, sdata)

    # 当用户点击“保存”按钮时，保存配置并关闭模态框
    @reactive.effect
    @reactive.event(input.save_config)
    def _():
        # 保存配置
        g_openai_config.set({"model_name": input.model_name_input(), 
                             "base_url": input.base_url_input(), 
                             "api_key": input.api_key_input()
                             })
        
        g_sdata.set({"paths": input.dir_chooser_path(),
                     "urls": input.url_chooser_path()
                     })

        # 显示成功通知
        ui.notification_show("✅ 配置已保存!", type="message", duration=5)
        # 关闭模态框
        ui.modal_remove()

    # 当用户点击“取消”按钮时，关闭模态框
    @reactive.effect
    @reactive.event(input.cancel_config)
    def _():
        ui.modal_remove()

    # 目录数据初始化
    @reactive.Effect
    @reactive.event(input.sdata_init_btn)
    def _():
        # 获取目录选择器输入的值
        target_dir = WIKIDOCU_QA_DIR
        selected_dir = input.dir_chooser_path().strip()

        # 创建目标目录
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)
            ui.notification_show(f"⚠️ 目标目录不存在，创建目录 {target_dir}", type="warning", duration=10)
        
        # 判断选择的目录或者文件是否存在
        if selected_dir and (os.path.isfile(selected_dir) or os.path.exists(selected_dir)):
            # 拷贝目录及文件
            ui.notification_show("⏳ 开始拷贝文件...", type="message", duration=10)
            # 情况目标目录
            clear_docs_folder(target_dir)
            cpoy_directory(selected_dir, target_dir)

        elif selected_dir:
            ui.notification_show(f"⚠️ 选择的路径不存在: {selected_dir}", type="warning", duration=10)
            return 

        # 获取 url_chooser_path 输入的值
        url_input = input.url_chooser_path()

        # 将输入的 URL 字符串转换为列表（支持换行符和逗号分隔）
        if url_input:
            # 使用换行符和逗号作为分隔符
            import re
            # 按换行符或逗号分割
            url_parts = re.split(r'[\n,]+', url_input)
            # 去除每个URL的首尾空格并过滤空字符串
            urls = [url.strip() for url in url_parts if url.strip()]
            # 去重但保持顺序
            seen = set()
            unique_urls = []
            for url in urls:
                if url not in seen:
                    seen.add(url)
                    unique_urls.append(url)
            urls = unique_urls
        else:
            urls = []

        # 处理URL并保存到target_dir
        if urls:
            # 确保target_dir存在
            os.makedirs(target_dir, exist_ok=True)

            success_count = 0
            for i, url in enumerate(urls):
                try:
                    # 获取网页内容
                    content = webfetch(url=url)
                    if content:
                        # 生成文件名（使用URL的一部分或索引）
                        filename = f"web_content_{i+1}.md"
                        # 也可以尝试从URL中提取文件名
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        if parsed_url.path:
                            url_filename = os.path.basename(parsed_url.path)
                            if url_filename and '.' in url_filename:
                                filename = url_filename
                        
                        # 确保文件名以.md结尾
                        if not filename.endswith('.md'):
                            filename += '.md'
                        
                        # 保存文件到target_dir
                        file_path = os.path.join(target_dir, filename)
                        with open(file_path, 'w', encoding='utf-8') as f:
                            # 在文件开头添加URL来源信息
                            f.write(f"# 来源: {url}\n\n")
                            f.write(content)

                        success_count += 1
                        ui.notification_show(f"✅ 成功保存URL内容到 {file_path}", type="message", duration=5)

                    else:
                        ui.notification_show(f"⚠️ 无法获取URL内容: {url}", type="warning", duration=5)
                except Exception as e:
                    ui.notification_show(f"❌ 处理URL时出错 {url}: {str(e)}", type="error", duration=5)
