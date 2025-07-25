# server.py

from shiny import render, reactive, ui
import os
import random
import datetime

from frontend.navset_builder import NavsetUIBuilder
from frontend.config import navset_configs
from frontend.utils import generate_full_report,clear_docs_folder,custom_box
from src.filecontentextract import FileContentExtract
from global_vars import ui_detail_output_handler, ui_main_outputt_handler, UI_DETAIL_OUTPUT_PATH,UI_MAIN_OUTPUTT_PATH


SCAN_DIR = "./docs"

ui_detail_output_handler.clear_file()
ui_main_outputt_handler.clear_file()
ui_main_outputt_handler.write_content("欢迎使用 **WikiDocu**！请在下方输入您的问题, 点击 **检索** 以开始分析。")


builder = NavsetUIBuilder(navset_configs)

'''
def setup_server(input, output, session):
    dynamic_ui_content = reactive.Value(ui.TagList())

    @output
    @render.text
    @reactive.file_reader(UI_DETAIL_OUTPUT_PATH)
    async def detail_output():
        try:
            if not os.path.exists(UI_DETAIL_OUTPUT_PATH) or not os.path.isfile(UI_DETAIL_OUTPUT_PATH):
                print(f"Log file does not exist: {UI_DETAIL_OUTPUT_PATH}")
                return "Log file not found."

            with open(UI_DETAIL_OUTPUT_PATH, "r", encoding='utf-8') as file:
                log_lines = file.readlines()
                return ui.HTML(f'<div style="font-size: 18px; background-color: #f0f0f0; padding: 10px;">{"".join(log_lines)}</div>')

        except Exception as e:
            return f"读取文件出错：{str(e)}"

    @output
    @render.text
    @reactive.file_reader(UI_MAIN_OUTPUTT_PATH)
    async def main_output():
        try:
            if not os.path.exists(UI_MAIN_OUTPUTT_PATH) or not os.path.isfile(UI_MAIN_OUTPUTT_PATH):
                print(f"Log file does not exist: {UI_MAIN_OUTPUTT_PATH}")
                return "Log file not found."

            with open(UI_MAIN_OUTPUTT_PATH, "r", encoding='utf-8') as file:
                log_lines = file.readlines()
                return ui.HTML(f'<div style="font-size: 18px; background-color: #f0f0f0; padding: 10px;">{"".join(log_lines)}</div>')

        except Exception as e:
            return f"读取文件出错：{str(e)}"

    @output
    @render.ui
    @reactive.event(input.add_more)
    def dynamic_content():
        navset_types = list(navset_configs.keys())
        selected_type = random.choice(navset_types)

        new_content = ui.TagList(
            builder.create_navset_ui(selected_type),
        )

        current_content = dynamic_ui_content.get()
        current_content.append(new_content)
        dynamic_ui_content.set(current_content)

        return dynamic_ui_content.get()

    @output
    @render.code
    def selected_values():
        selected = {}
        for navset_type in navset_configs.keys():
            for navset_id in navset_configs[navset_type].keys():
                component_id = f"{navset_type}_{navset_id}"
                if hasattr(input, component_id):
                    selected[component_id] = getattr(input, component_id)()
        return str(selected)

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

def setup_server(input, output,  session):
    dynamic_ui_content = reactive.Value(ui.TagList())

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

###############

    @output
    @render.ui
    @reactive.event(input.add_more)
    def dynamic_content():
        navset_types = list(navset_configs.keys())
        selected_type = random.choice(navset_types)

        new_content = ui.TagList(
            builder.create_navset_ui(selected_type),
        )

        current_content = dynamic_ui_content.get()
        current_content.append(new_content)
        dynamic_ui_content.set(current_content)

        return dynamic_ui_content.get()

    @output
    @render.code
    def selected_values():
        selected = {}
        for navset_type in navset_configs.keys():
            for navset_id in navset_configs[navset_type].keys():
                component_id = f"{navset_type}_{navset_id}"
                if hasattr(input, component_id):
                    selected[component_id] = getattr(input, component_id)()
        return str(selected)


##########
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

