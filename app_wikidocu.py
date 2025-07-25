# server.py

from shiny import App, ui, render, reactive
import os
import random
import datetime
from langchain_core.messages import BaseMessage, HumanMessage
import time  # 同步延迟使用


from src.graph import create_async_tools_graph
from frontend.navset_builder import NavsetUIBuilder
from frontend.config import navset_configs
from frontend.utils import generate_full_report,custom_box

SCAN_DIR = "./docs"

builder = NavsetUIBuilder(navset_configs)

# ========== Server Logic ==========
model_name = os.getenv("MODEL_NAME", "your-model-name")
model_name_answer = os.getenv("MODEL_NAME_QWEN3", "your-model-name")

base_url = os.getenv("OPENAI_BASE_URL", "your-base-url")
api_key = os.getenv("OPENAI_API_KEY", "your-api-key")

graph = create_async_tools_graph()
config = {"configurable": {"thread_id": "1"}}

def setup_server(input, output,  session):
    g_value_main_output = reactive.Value("")
    g_value_detail_output = reactive.Value("")
    dynamic_ui_content = reactive.Value(ui.TagList())

    m = ui.modal(
        ui.markdown(f"""
### 欢迎使用 **WikiDocu** —— 基于人工智能的多文档智能问答系统

在这里，你可以：

- 📚 **跨文档智能问答**：在多个文档之间建立关联，实现知识的跨文档检索与精准问答，支持复杂场景下的信息整合。
- 🧩 **深度知识理解**：融合代码理解与技术文档生成能力，可深入解析结构化内容（如代码仓库），实现从代码到文档的自动推理与解释。
- 🧠 **上下文感知交互**：支持基于上下文的多轮对话理解，智能定位相关内容，提升检索效率与准确性。
- 🛠 **无需索引构建**：无需预处理构建向量库或索引，直接利用大模型理解内容，部署更轻量，响应更迅速。

请将需要分析的文档放入目录 **`{SCAN_DIR}`**，然后输入你的问题，点击 **检索**，即可开启高效、智能的知识探索之旅。

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

    # 初始化 markdown 内容
    custom_box(input, output, session)

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

        #return dynamic_ui_content.get()
        return ui.div(
                dynamic_ui_content.get(),
                style="max-height: 800px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;"
            )
    @reactive.effect
    @reactive.event(input.custom_send)
    async def handle_custom_send_waiting_notion():

        research_topic = input.custom_message().strip()
        ui.update_text_area(  
            id="custom_message",  
            value=""  # 设置为空字符串  
        )
        if not research_topic:
            ui.notification_show("⚠️ 请先输入研究主题。", type="error", duration=10 ) # 显式设置为右上角
            return

        # 显示加载提示 + 失效按键
        ui.notification_show("⏳ 正在分析，请稍候...", type="message", duration=10 )
        ui.update_action_button("custom_send", disabled=True)


    @reactive.effect
    @reactive.event(input.custom_send)
    async def handle_custom_send():
        research_topic = input.custom_message().strip()
        ui.update_text_area(  
            id="custom_message",  
            value=""  # 设置为空字符串  
        )
        input_path = SCAN_DIR #input.input_file_paths().strip()

        if not research_topic:
            ui.update_action_button("custom_send", disabled=False)
            return

        if not input_path or input_path == '.':
            file_paths = [os.path.abspath(os.getcwd())]
        else:
            file_paths = [os.path.abspath(input_path.replace('\\', os.sep).replace('/', os.sep))]

        try:
            response = await graph.ainvoke({"messages": [HumanMessage(content=research_topic)]
                                            }, config)

            if response.get("messages"):
                answer_resp = response["messages"][-1].content

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


# ========== 启动应用 ==========
from shiny import App, ui
from app_wikidocu import setup_server

app_ui = ui.page_fluid(
    # 自定义 CSS 样式
    ui.tags.style("""
        .shiny-modal-backdrop {
            display: none !important;
        }
        #dynamic_content {
            overflow: visible !important;
            min-height: auto;
            height: auto !important;
        }
        .content-wrapper {
            overflow-y: auto;  /* 允许垂直滚动 */
        }
    """),
    
    # 用 div 包裹 dynamic_content 并添加 id 用于 JS 操作
    ui.div(
        ui.output_ui("dynamic_content"),
        class_="content-wrapper",
        style = "width: 100%; overflow: hidden;"
    ),
    
    # 页面底部自动滚动的 JavaScript 脚本
    ui.tags.script("""
        (function() {
            const observer = new MutationObserver(function() {
                const container = document.querySelector('.content-wrapper');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            });

            const target = document.querySelector('.content-wrapper');
            if (target) {
                observer.observe(target, { childList: true, subtree: true });
            }
        })();
    """)
)
app_ui2 = ui.page_fluid(
    ui.tags.style("""
        .shiny-modal-backdrop {
            display: none !important;
        }
        #dynamic_content {
            overflow: visible !important;
            height: auto !important;
            min-height: unset !important;
        }
    """),
    
    ui.br(),
    ui.markdown(f"""
    ### 欢迎使用 **WikiDocu** —— 基于人工智能的多文档智能问答系统

    在这里，你可以：

    - 📚 **跨文档智能问答**：在多个文档之间建立关联，实现知识的跨文档检索与精准问答，支持复杂场景下的信息整合。
    - 🧩 **深度知识理解**：融合代码理解与技术文档生成能力，可深入解析结构化内容（如代码仓库），实现从代码到文档的自动推理与解释。
    - 🧠 **上下文感知交互**：支持基于上下文的多轮对话理解，智能定位相关内容，提升检索效率与准确性。
    - 🛠 **无需索引构建**：无需预处理构建向量库或索引，直接利用大模型理解内容，部署更轻量，响应更迅速。

    请将需要分析的文档放入目录 **`{SCAN_DIR}`**，然后输入你的问题，点击 **检索**，即可开启高效、智能的知识探索之旅。

    """),
    ui.br(),
    ui.output_ui("dynamic_content"),
)


app = App(app_ui, setup_server)

if __name__ == "__main__":
    app.run()
