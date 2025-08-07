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

def show_api_config_modal(input, output, session, openai_config):
    """
    显示一个模态框，用于配置 API 密钥、模型名称和基础 URL。
    这些值将被存储在 Shiny 的会话变量中。
    """
    # 从环境变量或会话中获取当前值，如果都没有则为空
    current_api_key = openai_config.get("api_key")
    current_model =  openai_config.get("model_name")
    current_base_url = openai_config.get("base_url")

    # 创建模态框内容
    m = ui.modal(
        ui.markdown("#### 配置模型参数"),
        # API Key 输入框
        ui.input_password(
            "api_key_input",
            ui.HTML("<strong>API Key:</strong>"),
            value=current_api_key,
            width="100%"
        ),
        ui.br(),
        # Model Name 输入框
        ui.input_text(
            "model_name_input",
            ui.HTML("<strong>模型名称 (MODEL_NAME):</strong>"),
            value=current_model,
            width="100%"
        ),
        ui.br(),
        # Base URL 输入框
        ui.input_text(
            "base_url_input",
            ui.HTML("<strong>基础 URL (OPENAI_BASE_URL):</strong>"),
            value=current_base_url,
            width="100%"
        ),
        ui.br(),
        # 确认和取消按钮
        ui.div(
            ui.input_action_button("save_config", "保存", class_="btn btn-success"),
            ui.input_action_button("cancel_config", "取消", class_="btn btn-secondary"),
            style="display: flex; justify-content: space-between;"
        ),
        title="模型配置",
        easy_close=False, # 禁用点击背景关闭，强制用户使用按钮
        footer=None
    )
    # 显示模态框
    ui.modal_show(m)

def custom_box(input, output, session):
    # 自定义输入框样式：更现代、半透明的固定底部栏
    custom_style = """
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.95); /* 更高的不透明度 */
        border-top: 1px solid #ddd;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        z-index: 9999;
        padding: 15px;
        font-family: sans-serif;
    """
    # 创建 div 内容（注意顺序和参数）
    content = ui.div(
        # 使用更语义化的标签和更清晰的提示
        ui.input_text_area("custom_message",
                           ui.HTML("<strong>请输入您的问题 🔍 :</strong>"),
                           rows=2, width="100%", 
                           # 提供一个更具引导性的默认问题
                           value="请分析文档，并总结其主要内容。",
                           ),
        ui.br(),
        ui.div(
            # 添加一个配置按钮
            ui.input_action_button("open_config", "⚙️ 配置", class_="btn btn-outline-secondary"),
            # 为按钮添加了更现代的样式类和表情符号
            ui.input_action_button("custom_send", "🔍 检索", class_="btn btn-primary btn-lg"),
            style="""
                display: flex;
                justify-content: center; /* 水平居中 */
                align-items: center; /* 垂直居中（如果需要的话） */
                gap: 15px; /* 控件之间的间距 */
            """
        ),
        id="custom_bottom_modal",
        style=custom_style
    )

    # 插入到页面底部
    ui.insert_ui(
        selector="body",
        where="beforeEnd",
        ui=content
    )
