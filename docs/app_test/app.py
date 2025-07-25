# app.py

from shiny import App, ui
from app_wikidocu import setup_server


app_ui = ui.page_fluid(
    ui.h1("动态创建多个 ui.navset_card 示例"),
    ui.hr(),
    ui.input_action_button("add_more", "添加更多组件"),
    ui.output_ui("dynamic_content"),
)

app = App(app_ui, setup_server)

if __name__ == "__main__":
    app.run()
