from shiny import App, render, ui, reactive
from typing import Dict, Any
import random

# 配置字典
navset_configs: Dict[str, Dict[str, Dict[str, Any]]] = {
    "navset_card_tab": {
        "对话": {"title": "Tab Card"},
    #    "with_sidebar": {"title": "Tab with Sidebar", "sidebar": ui.sidebar("Sidebar content")},
    },
    # "navset_card_pill": {
    #     "default": {"title": "Pill Card"},
    #     "below": {"title": "Pill Below", "placement": "below"},
    # },
    # "navset_card_underline": {
    #     "default": {"title": "Underline Card"},
    #     "with_header": {"title": "With Header", "header": "Header content"},
    # },
}

def create_navset_ui(navset_type: str) -> list:
    """动态创建 navset 组件的 UI"""
    navset_function = getattr(ui, navset_type)
    components = []

    for navset_id, params in navset_configs[navset_type].items():
        navset_kwargs = params.copy()

        # 创建导航面板
        nav_panels = []
        #for suffix in ["a", "b"]:
        panel_id = f"{navset_type}_1"
        
        # 创建左右布局的内容
        left_content = ui.div("左侧内容", style="border:1px solid #ccc; padding:10px;")
        right_content = ui.div("右侧内容", style="border:1px solid #ccc; padding:10px;")
        
        body_content = ui.row(
            ui.column(6, left_content),
            ui.column(6, right_content)
        )
        
        nav_panels.append(
            ui.nav_panel(panel_id, body_content, value=panel_id)
        )

        # 创建 navset 组件
        component = navset_function(
            *nav_panels,
            id=f"{navset_type}_{navset_id}",
            **navset_kwargs
        )

        components.append(ui.div(
            ui.h4(f"{navset_type} - {navset_id}"),
            component,
            style="margin-bottom: 2rem;"
        ))

    return components

# 构建 UI
app_ui = ui.page_fluid(
    ui.h1("动态创建多个 ui.navset_card 示例"),
    ui.hr(),
    ui.input_action_button("add_more", "添加更多组件"),
    ui.output_ui("dynamic_content"),
    #ui.h3("当前选中的值:"),
    #ui.output_code("selected_values")
)

def server(input, output, session):
    # 用 reactive.Value 保存累计的 UI 内容
    dynamic_ui_content = reactive.Value(ui.TagList())

    @render.ui
    @reactive.event(input.add_more)
    def dynamic_content():
        navset_types = list(navset_configs.keys())
        selected_type = random.choice(navset_types)  # 随机选择一个类型

        # 生成新内容
        new_content = ui.TagList(
            #ui.h4(f"第 {len(dynamic_ui_content.get()) + 1} 次添加的组件（{selected_type}）"),
            create_navset_ui(selected_type),
        )

        # 追加到已有内容中
        current_content = dynamic_ui_content.get()
        current_content.append(new_content)
        dynamic_ui_content.set(current_content)

        return dynamic_ui_content.get()  # 返回全部内容

    # 显示所有选中的值
    @render.code
    def selected_values():
        selected = {}
        for navset_type in navset_configs.keys():
            for navset_id in navset_configs[navset_type].keys():
                component_id = f"{navset_type}_{navset_id}"
                if hasattr(input, component_id):
                    selected[component_id] = getattr(input, component_id)()
        return str(selected)

app = App(app_ui, server)

if __name__ == "__main__":
    app.run()