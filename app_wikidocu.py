# app_wikidocu.py

from shiny import App, ui, render, reactive
import os
import random
import datetime
from langchain_core.messages import BaseMessage, HumanMessage
import time  # 同步延迟使用

from frontend.navset_builder import NavsetUIBuilder
from frontend.components import create_auto_scroll_div
from frontend.config import navset_configs
from frontend.utils import generate_full_report, show_api_config_modal, custom_research_body
from src.func_utils import cpoy_directory
from src.graph import create_async_tools_graph

SCAN_DIR = "./docs"
builder = NavsetUIBuilder(navset_configs)

# ========== Server Logic ==========
# 初始化时从环境变量获取默认值
api_key = os.getenv("OPENAI_API_KEY", "sk-xxx")
model_name = os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-7B-Instruct")
model_name_answer= os.getenv("OPENAI_MODEL", "Qwen/Qwen2.5-7B-Instruct")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")

def setup_server(input, output,  session):
    g_value_main_output = reactive.Value("")
    g_value_detail_output = reactive.Value("")
    dynamic_ui_content = reactive.Value(ui.TagList())
    g_openai_config=reactive.Value({"model_name": model_name, "base_url": base_url, "api_key": api_key})

    # 显示欢迎模态框
    m = ui.modal(
        ui.markdown(f"""
### 欢迎使用 **WikiDocu** —— 基于人工智能的多文档智能问答系统

你可以：

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

    
    # 初始化 markdown 内容和底部输入栏
    custom_research_body(input, output, session)

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
        input_path = SCAN_DIR

        if not research_topic:
            ui.update_action_button("custom_send", disabled=False)
            return

        # 1. 获取用户配置或使用默认值
        config=g_openai_config.get()
        user_api_key = config.get("api_key")
        user_model_name =  config.get("model_name")
        user_base_url = config.get("base_url")

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
        show_api_config_modal(input, output, session, openai_config)

    # 当用户点击“保存”按钮时，保存配置并关闭模态框
    @reactive.effect
    @reactive.event(input.save_config)
    def _():
        # 保存配置
        g_openai_config.set({"model_name": input.model_name_input(), 
                             "base_url": input.base_url_input(), 
                             "api_key": input.api_key_input()}
                             )

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
    @reactive.event(input.dir_check_btn)
    def _():
        target_dir = SCAN_DIR
        selected_dir = input.dir_chooser_path().strip()

        # 创建目标目录
        if not os.path.exists(selected_dir):
            ui.notification_show("⚠️ 目标目录不存在", type="error", duration=10)
        else:
            # 拷贝目录及文件
            ui.notification_show("⏳ 初始化开始...", type="message", duration=10)
            cpoy_directory(selected_dir, target_dir)
            



# ==============================================================
#                        启动应用
# ==============================================================
# 定义应用的用户界面
app_ui = ui.page_fluid(
    # 自定义 CSS 样式
#     ui.tags.style("""
#         /* 隐藏模态框的背景遮罩 */
#         .shiny-modal-backdrop {
#             display: none !important;
#         }
        
#         /* 动态内容区域样式 */
#         #dynamic_content {
#             overflow: visible !important;
#             min-height: auto;
#             height: auto !important;
#         }
        
#         /* 内容包装器样式：允许垂直滚动 */
#         .content-wrapper {
#             background-color: rgba(255, 255, 255, 0); /* 背景透明度 */
#             overflow-y: auto;
#             max-height: calc(100vh - 100px); /* 预留顶部和底部空间 */
#         }
        
#         /* 卡片 header 样式 */
#         .card-header {
#             background-color: rgba(255, 255, 255, 0); /* 背景透明度 */
#             border-bottom: 1px solid #e9ecef;
#             font-weight: bold;
#             padding: 10px 15px;
#         }
        
#         /* 卡片 body 样式 */
#         .card-body {
#             padding: 15px;
#             background-color: rgba(255, 255, 255, 0); /* 背景透明度 */
#             border: 1px solid rgba(0, 0, 0, 0.15);       /* 边框颜色 */
#             padding: 10px 16px;                         /* 内边距 */
#             box-shadow: 0 2px 10px rgba(0, 0, 0, 0); /* 柔和阴影 */
#             backdrop-filter: blur(8px);                /* 毛玻璃效果 */
# }
#     """),
    ui.tags.style("""
        /* ========== 隐藏模态框遮罩 ========== */
        .shiny-modal-backdrop {
            display: none !important;
        }
        
        /* ========== 动态内容区域 ========== */
        #dynamic_content {
            overflow: visible !important;
            min-height: auto;
            height: auto !important;
        }
        
        /* ========== 内容包装器：允许垂直滚动 ========== */
        .content-wrapper {
            background-color: rgba(255, 255, 255, 0); /* 完全透明 */
            overflow-y: auto;
            max-height: calc(100vh - 100px);
        }
        
        /* ========== 卡片 header：仅保留文字样式，去边框 ========== */
        .card-header {
            background-color: rgba(255, 255, 255, 0); /* 透明背景 */
            border-bottom: none;           /* 🔴 移除边框 */
            font-weight: bold;
            padding: 10px 15px;
            color: #000000;                /* 可选：设为白色文字 */
        }
        
        /* ========== 卡片 body：完全透明，无边框、无阴影、无模糊 ========== */
        .card-body {
            background-color: rgba(255, 255, 255, 0); /* 透明背景 */
            border: none;                  /* 🔴 移除边框 */
            box-shadow: none;              /* 🔴 移除阴影 */
            padding: 15px;                 /* 保留内边距保证可读性 */
        }
    """),
    ui.markdown(f"""### 欢迎使用 ***WikiDocu***"""),

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

# 创建 Shiny 应用实例
app = App(app_ui, setup_server)

# 如果作为主模块运行，则启动应用
if __name__ == "__main__":
    app.run()
