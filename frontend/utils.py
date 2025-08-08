
from shiny import ui

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

        #ui.input_file("dir_chooser_btn",  ui.markdown("#### 选择要探索的文件"), multiple=True, width="100%"),
        ui.markdown("#### I.配置源文件"),
        ui.input_text("dir_chooser_path", "源文件(目录)", value="./docs", placeholder="输入目录地址...", width="100%"),
        ui.input_action_button(
            "dir_check_btn", "▶️ 开始初始化...",
            #class_="btn btn-success btn-sm",  # 使用 Bootstrap 按钮样式
            style="padding: 0.375rem 1rem; font-size: 0.875rem;"
        ),
        # 分割线
        ui.tags.hr(style="margin: 1rem 0; border-top: 1px solid #ddd;"),

        # 配置标题
        ui.markdown("#### II.配置模型参数"),
        ui.tags.hr(style="margin: 0.5rem 0; border-top: 1px dashed #ccc;"),

        # 模型名称输入
        ui.input_text(
            "model_name_input",
            ui.HTML("<strong>模型名称 (MODEL_NAME):</strong>"),
            value=current_model,
            width="100%",
            placeholder="例如：qwen-max"
        ),

        # API Key 输入
        ui.input_password(
            "api_key_input",
            ui.HTML("<strong>API Key:</strong>"),
            value=current_api_key,
            width="100%",
            placeholder="请输入您的 API 密钥"
        ),

        # Base URL 输入
        ui.input_text(
            "base_url_input",
            ui.HTML("<strong>基础 URL (OPENAI_BASE_URL):</strong>"),
            value=current_base_url,
            width="100%",
            placeholder="例如：https://api.bailian.ai/api/v1"
        ),

        # 换行
        ui.br(),

        # 按钮：右对齐，加大按钮
        ui.div(
            ui.input_action_button(
                "save_config", "💾 保存",
                class_="btn btn-success btn-sm",  # 使用 Bootstrap 按钮样式
                style="padding: 0.375rem 1rem; font-size: 0.875rem;"
            ),
            ui.input_action_button(
                "cancel_config", "↩️ 取消",
                class_="btn btn-secondary btn-sm",
                style="padding: 0.375rem 1rem; font-size: 0.875rem;"
            ),
            style="display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.5rem;"
        ),

        #title="配置信息",
        easy_close=False, # 禁用点击背景关闭，强制用户使用按钮
        footer=None
    )
    # 显示模态框
    ui.modal_show(m)

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
                    value="请分析文档，并总结其主要内容。",
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
                "🔍 提问",
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