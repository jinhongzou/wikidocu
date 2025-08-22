# app_wikidocu.py
from shiny import App, ui, render, reactive

# 定义应用的用户界面
from frontend.ui_wikidocu import  ui_wikidocu
from frontend.ui_podcast import ui_podcast

# Import Podcast-LLM components
from frontend.server_podcast_llm import podcast_llm_server
from frontend.server_wikidocu import wikidocu_server

# Import custom research body functions
from frontend.utils_wikidocu import custom_research_body, remove_custom_research_body, restore_custom_research_body

import logging
from config.logging_config import setup_logging

# ==============================================================
#                        设置日志
# ==============================================================
from config.global_vars import LOG_LVL, LOG_FILE
log_level = logging.DEBUG if LOG_LVL else logging.INFO
setup_logging(log_level, output_file=LOG_FILE)

# ==============================================================
#                        启动应用
# ==============================================================
app_ui = ui.page_navbar(
    ui.nav_panel("WikiDocu", ui_wikidocu),
    ui.nav_panel("Podcast", ui_podcast),
    title="WikiDocu & Podcast",
    id="main_navbar"
)

# 创建主服务器逻辑，根据当前导航面板选择相应的服务器逻辑
def main_server(input, output, session):
    # 初始化 WikiDocu 服务器逻辑
    wikidocu_server(input, output, session)

    # 初始化 Podcast-LLM 服务器逻辑
    podcast_llm_server(input, output, session)
    
    # 添加自定义研究输入栏
    custom_research_body(input, output, session)
    
    # 监听导航栏变化，根据当前面板显示/隐藏自定义研究输入栏
    @reactive.Effect
    @reactive.event(input.main_navbar)
    def _():
        current_tab = input.main_navbar()
        if current_tab == "WikiDocu":
            # 恢复自定义研究输入栏
            restore_custom_research_body(input, output, session)
        elif current_tab == "Podcast":
            # 移除自定义研究输入栏
            remove_custom_research_body()

# 创建 Shiny 应用实例
app = App(app_ui, main_server)

# 启动应用
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
