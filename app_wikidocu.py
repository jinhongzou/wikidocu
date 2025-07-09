from shiny import App, ui, render, reactive, Session
import os
import datetime
import markdown  # 可选：用于前端渲染支持
import shutil

from src.filecontentextract import FileContentExtract

from frontend.utils import generate_full_report,clear_docs_folder,custom_box

SCAN_DIR = "./docs"

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
                ui.output_ui("detail_output"),
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

model_name = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct")
base_url = os.getenv("OPENAI_BASE_URL", "https://api.siliconflow.cn/v1")
api_key = os.getenv("OPENAI_API_KEY", "sk-xxx")


def server(input, output,  session):
    # 初始化 markdown 内容
    g_value_main_output = reactive.Value("欢迎使用 WikiDocu！请在下方输入研究主题并选择文件路径以开始分析。")
    g_value_detail_output=reactive.Value("")

    async def perform_analysis(research_topic, file_paths):

        researcher = FileContentExtract(
            model=model_name,
            api_key=api_key,
            api_base=base_url,
            name='ResearcherAgent'
        )

        all_results = await researcher.async_run(
            file_paths=file_paths,
            research_topic=research_topic
        )

        content = researcher.get_markdown_ref()
        answer = researcher.final_answer(research_topic=research_topic, content=content)
        return (answer, content)



    custom_box(input, output, session)

    @output
    @render.ui
    def main_output():
        content = g_value_main_output.get()
        #print("main_output当前内容长度:", len(content))  # 验证是否刷新

        return ui.HTML(f'<div style="font-size: 18px; background-color: #f0f0f0; padding: 10px;">{ui.markdown(content)}</div>')
    
    @output
    @render.ui
    def detail_output():
        content = g_value_detail_output.get()
        #print("detail_output当前内容长度:", len(content))  # 验证是否刷新

        return ui.markdown(content)


    @reactive.effect
    @reactive.event(input.choose_dir)
    def dir_list():
        
        target_dir = SCAN_DIR

        # ✅ 先清空 docs 目录
        """
        if not clear_docs_folder(docs_path=target_dir):
            return []
        """

        selected_dir = input.dir_path().strip()
        if not selected_dir:
            return []

        os.makedirs(target_dir, exist_ok=True)

        all_files = []

        for root, _, files in os.walk(selected_dir):
            rel_path = os.path.relpath(root, selected_dir)
            dest_subdir = os.path.join(target_dir, rel_path)
            os.makedirs(dest_subdir, exist_ok=True)

            for f in files:
                src_file = os.path.join(root, f)
                dest_file = os.path.join(dest_subdir, f)

                try:
                    shutil.copy2(src_file, dest_file)  # 拷贝并保留元数据
                    all_files.append(dest_file)
                    print(f"✅ 已复制：{src_file} → {dest_file}")
                except Exception as e:
                    print(f"❌ 复制失败：{src_file}，错误：{str(e)}")

        return all_files
    

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
            (answer, markdown_ref) = await perform_analysis(research_topic, file_paths)

            # ✅ 修改输出内容：添加标题、时间戳、数据源等内容
            timestamp = datetime.datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")

            if not answer.strip():
                full_report = "⚠️ 没有获取到有效的分析结果，请检查输入数据或稍后重试。"
            else:
                full_report = generate_full_report(research_topic, answer, file_paths, timestamp)

            g_value_main_output.set(full_report)
            g_value_detail_output.set(markdown_ref)

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
