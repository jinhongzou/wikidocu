from shiny import App, ui, render, reactive
import os
import datetime


from frontend.utils import generate_full_report,custom_box
from global_vars import ui_detail_output_handler, ui_main_outputt_handler, UI_DETAIL_OUTPUT_PATH,UI_MAIN_OUTPUTT_PATH

SCAN_DIR = "./docs"

ui_detail_output_handler.clear_file()
ui_main_outputt_handler.clear_file()
ui_main_outputt_handler.write_content("欢迎使用 **WikiDocu**！请在下方输入您的问题, 点击 **检索** 以开始分析。")

# ========== UI ==========
app_ui = ui.page_fluid(
    ui.tags.style("""
            .shiny-modal-backdrop {
                display: none !important;
            }"""
    ),
    ui.row(
        ui.column(
            6,
            ui.card(
                ui.card_header("WikiDocu"),
                ui.output_ui("main_output"),  # 使用 output_ui 替代 output_markdown
                style="height: 500px; overflow-y: auto;"
            )
        ),
        ui.column(
            6,
            ui.card(
                ui.card_header("检索结果"),
                #ui.output_ui("detail_output"),
                ui.output_ui("detail_output"),  # Use selected value

                style="height: 500px; overflow-y: auto;"
            )
        )
    ),
)
'''
    ui.row(
        ui.column(
            6,
            ui.card(
                ui.card_header("检索文件列表"),
                #ui.input_text("input_file_paths", "请输入查询目录（默认当前目录）", value="D:/github_rep/gemini-fullstack-langgraph-quickstart/testfiles/README.md"),
                ui.row(
                    ui.column(12,
                        ui.input_text("dir_path", "选中的目录路径", value="", width="100%"),
                        ui.input_action_button("choose_dir", "加载文件", onclick="chooseDirectory()", class_="btn-primary")
                    )
                ),
                style="height: 400px; overflow-y: auto;"
            )
        ),
        ui.column(
            6,
            ui.card(
                #ui.card_header("输入框"),
                ui.card_header("日志"),
                ui.column(12,
                    #ui.input_text_area("custom_message", "请输入研究主题", value="怎么创建PydanticAgent实例", width="100%"),
                    #ui.input_checkbox("deep_research", "启用深度研究", False),
                    #ui.input_action_button("submit", "开始分析")
                ),
                style="height: 300px; overflow-y: auto;"
            )
        )
    )
'''

# ========== Server Logic ==========
from shiny import App, ui, render, reactive
import os
import asyncio
from src.filecontentextract import FileContentExtract

model_name = os.getenv("MODEL_NAME", "your-model-name")
model_name_answer = os.getenv("MODEL_NAME_QWEN3", "your-model-name")

base_url = os.getenv("OPENAI_BASE_URL", "your-base-url")
api_key = os.getenv("OPENAI_API_KEY", "your-api-key")

from langchain_core.messages import BaseMessage, HumanMessage
from src.graph import create_async_tools_graph

graph = create_async_tools_graph()
config = {"configurable": {"thread_id": "1"}}

def server(input, output,  session):
    # 初始化 markdown 内容
    g_value_main_output = reactive.Value("欢迎使用 WikiDocu！请在下方输入研究主题并选择文件路径以开始分析。")

    custom_box(input, output, session)

    @output
    @render.text
    @reactive.file_reader(UI_DETAIL_OUTPUT_PATH)
    async def detail_output():  # Added function declaration
        try:
            # 读取日志文件
            # 检查文件是否存在并且是一个文件
            if not os.path.exists(UI_DETAIL_OUTPUT_PATH) or not os.path.isfile(UI_DETAIL_OUTPUT_PATH):
                print(f"Log file does not exist: {UI_DETAIL_OUTPUT_PATH}")
                return "Log file not found."

            # 使用内置方法读取文本文件
            with open(UI_DETAIL_OUTPUT_PATH, "r", encoding='utf-8') as file:
                log_lines = file.readlines()  # 读取所有行
                return  ui.HTML(f'<div style="font-size: 18px; background-color: #f0f0f0; padding: 10px;">{ui.markdown(''.join(log_lines))}</div>')
        except Exception as e:
            return f"读取文件出错：{str(e)}"


    @output
    @render.text
    @reactive.file_reader(UI_MAIN_OUTPUTT_PATH)
    async def main_output():  # Added function declaration
        try:
            # 读取日志文件
            # 检查文件是否存在并且是一个文件
            if not os.path.exists(UI_MAIN_OUTPUTT_PATH) or not os.path.isfile(UI_MAIN_OUTPUTT_PATH):
                print(f"Log file does not exist: {UI_MAIN_OUTPUTT_PATH}")
                return "Log file not found."

            # 使用内置方法读取文本文件
            with open(UI_MAIN_OUTPUTT_PATH, "r", encoding='utf-8') as file:
                log_lines = file.readlines()  # 读取所有行
                return  ui.HTML(f'<div style="font-size: 18px; background-color: #f0f0f0; padding: 10px;">{ui.markdown(''.join(log_lines))}</div>')
        except Exception as e:
            return f"读取文件出错：{str(e)}"

    @reactive.effect
    @reactive.event(input.custom_send)
    async def handle_custom_send_waiting_notion():
        research_topic = input.custom_message().strip()
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

            answer = response["messages"][-1].content
            #print(f">>> type: {type(answer)}\n{answer}")
            # ✅ 修改输出内容：添加标题、时间戳、数据源等内容
            timestamp = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

            if not answer.strip():
                full_report = "⚠️ 没有获取到有效的分析结果，请检查输入数据或稍后重试。"
            else:
                full_report = generate_full_report(research_topic, answer, file_paths, timestamp)

            g_value_main_output.set(full_report)

            # 如果是第一轮对话，清除欢迎词
            if ui_main_outputt_handler._turns == 0:
                ui_main_outputt_handler.clear_file()

            ui_main_outputt_handler._turns=ui_main_outputt_handler._turns + 1
            ui_main_outputt_handler.write_content(f"---\n### 第 [{ui_main_outputt_handler._turns}] 轮对话\n{full_report}\n")

        except Exception as e:
            ui.notification_show(f"❌ 分析过程中发生错误：{str(e)}", type="error", duration=10 )
            g_value_main_output.set("⚠️ 分析过程中发生错误，请重试。")
        finally:
            # 无论成功与否，都启用按钮
            ui.update_action_button("custom_send", disabled=False)


# ========== 启动应用 ==========
app = App(app_ui, server)
if __name__ == "__main__":
    app.run()
