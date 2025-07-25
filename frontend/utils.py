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

> 🕒***{timestamp}*** ⚠️ 注：以上分析基于当前输入的数据文件和模型理解能力，仅供参考。"""

def custom_box(input, output, session):
    # 自定义样式（字符串）
    custom_style = """
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: rgba(128, 128, 128, 0.5); /* 更高的透明度 */
        border-top: 1px solid #ccc;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
        z-index: 9999;
        padding: 10px;
        font-family: sans-serif;
    """
    # 创建 div 内容（注意顺序和参数）
    content = ui.div(
        ui.input_text_area("custom_message",
                           ui.HTML("<strong>你的问题🔍:</strong>"),
                           rows=2, width="100%", 
                           value="检索文件，并简单介绍这份文件内容",
                           ),
        ui.br(),
        ui.div(
            ui.input_switch("deep_research", "Deep Research", value=False),
            ui.input_action_button("custom_send", "检索🔍...", class_="btn btn-primary"),
            style="""
                display: flex;
                justify-content: center; /* 水平居中 */
                align-items: center; /* 垂直居中（如果需要的话） */
                gap: 10px; /* 控件之间的间距 */
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
