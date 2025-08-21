import shutil
import os
from shiny import App, ui, render, reactive, Session

def generate_full_report(research_topic, answer, file_paths, timestamp):
    """
    生成完整的分析报告内容（Markdown 格式）
    """
    return f"""
#### {research_topic}

---

{answer}

> 🕒 ***{timestamp}***  \n> ⚠️ *注：以上分析基于当前输入的数据文件和模型理解能力，仅供参考。*
"""

def show_api_config_modal(input, output, session, openai_config, sdata):
    """
    Show the API configuration modal.
    
    Args:
        input: Shiny input object
        output: Shiny output object
        session: Shiny session object
        openai_config: Current OpenAI configuration
        sdata: Current data configuration
    """
    # Create the modal content
    modal_content = ui.TagList(
        ui.div(
            ui.h5("⚙️ API 配置"),
            ui.input_text("model_name_input", "模型名称", value=openai_config.get("model_name", "")),
            ui.input_text("base_url_input", "API 基础 URL", value=openai_config.get("base_url", "")),
            ui.input_password("api_key_input", "API 密钥", value=openai_config.get("api_key", "")),
            class_="mb-3"
        ),
        ui.div(
            ui.tags.hr(style="margin: 1rem 0; border-top: 1px solid #ddd;"),
            ui.h5("📁 数据源配置"),
            ui.input_text("dir_chooser_path", "文件加载目录", value="dataset", placeholder="输入目录地址...", width="100%"),
            ui.input_text_area("url_chooser_path", "URL列表 (每行一个)", value=sdata.get("urls", ""), rows=1),
            ui.input_action_button("sdata_init_btn", "▶️ 开始初始化...", class_="btn btn-primary me-3"),
            class_="mb-3"

        ),
        ui.div(
            ui.input_action_button("save_config", "💾 保存", class_="btn btn-primary me-2"),
            ui.input_action_button("cancel_config", "❌ 取消", class_="btn btn-secondary"),
            class_="d-flex justify-content-end"
        )
    )
    
    # Create and show the modal
    modal = ui.modal(
        modal_content,
        title="配置设置",
        easy_close=False,
        footer=None
    )
    ui.modal_show(modal)

def custom_research_body(input, output, session):
    # 外层固定栏样式（居中，最大宽度限制）
    custom_style = """
        position: fixed;
        bottom: 0;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 1200px;
        border-radius: 25px;
        background-color: rgba(255, 255, 255, 0.0);
        border-top: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
        z-index: 9999;
        padding: 12px 20px;
        font-family: 'Segoe UI', sans-serif;
    """

    # 水平主容器（flex 布局）
    container_style = """
        display: flex;
        align-items: center;
        gap: 12px;
        width: 100%;
    """

    # 输入框容器：自适应宽度，靠左输入
    input_container_style = """
        flex-grow: 1;
        min-width: 300px;
        background-color: rgba(255, 255, 255, 0); /* 背景透明度 */
        border: 1px solid rgba(0, 0, 0, 0.15);       /* 边框颜色 */
        border-radius: 16px;                        /* 更大的圆角 */
        padding: 10px 16px;                         /* 内边距 */
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0); /* 柔和阴影 */
        backdrop-filter: blur(8px);                /* 毛玻璃效果 */
        display: flex;
        justify-content: center;                     /* 水平靠左 */
        align-items: center;                       /* 垂直居中 */
        position: relative;                        /* 相对定位 */
        width: 80%;                               /* 占据80%宽度 */
    """

    # 按钮通用样式
    button_style = """
        height: 40px;
        border-radius: 10px;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease;
        white-space: nowrap;
        padding: 0 16px;
    """

    config_button_style = button_style + """
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        color: #555;
    """

    send_button_style = button_style + """
        background-color: #007bff;
        color: white;
        border: none;
        font-weight: bold;
    """

    # 构建 UI
    content = ui.div(
        ui.div(
            # 将输入框放入一个带样式的 div 容器中
            ui.div(
                ui.input_text_area(
                    "custom_message",
                    label=None,
                    placeholder="请输入您的问题，例如：请总结文档的主要内容...",
                    value="请分析文档，并总结其主要内容",
                    rows=1,
                    autoresize=True,
                    width="100%"
                ),
                style=input_container_style
            ),
            # 配置按钮
            ui.input_action_button(
                "open_config",
                "⚙️ 配置",
                class_="btn",
                style=config_button_style
            ),
            # 发送按钮
            ui.input_action_button(
                "custom_send",
                "🔍 检索",
                class_="btn",
                style=send_button_style
            ),
            style=container_style
        ),
        id="custom_bottom_bar",
        style=custom_style
    )

    # 插入页面底部
    ui.insert_ui(
        selector="body",
        where="beforeEnd",
        ui=content
    )


def remove_custom_research_body():
    """
    移除自定义研究输入栏
    """
    # 使用 JavaScript 移除插入的 UI 元素
    from shiny import ui
    # 如果 ui.remove_ui 方法不可用，使用 JavaScript 方式
    try:
        ui.remove_ui(
            selector="#custom_bottom_bar"
        )
    except AttributeError:
        # 如果 remove_ui 方法不存在，使用 JavaScript
        ui.tags.script("""
            document.addEventListener('DOMContentLoaded', function() {
                var element = document.getElementById('custom_bottom_bar');
                if (element) {
                    element.remove();
                }
            });
        """)


def restore_custom_research_body(input, output, session):
    """
    恢复自定义研究输入栏
    """
    # 首先尝试移除可能存在的旧元素（防止重复）
    try:
        remove_custom_research_body()
    except:
        pass
    
    # 重新添加自定义研究输入栏
    custom_research_body(input, output, session)
