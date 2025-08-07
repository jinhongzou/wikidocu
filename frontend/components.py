# components.py

from shiny import ui

def layout_box(main_content, detail_content):
    """创建一个左右分栏的布局，左侧为主内容，右侧为详细内容（如检索结果）。
    使用卡片（card）组件包装内容，并设置滚动条和最大高度。
    """
    return ui.row(
        ui.column(
            6,
            ui.card(
                ui.card_header("WikiDocu"),
                main_content,
                # 设置主内容区域样式：添加内边距、最大高度和垂直滚动条
                style="padding: 20px; max-height: 800px; overflow-y: auto; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"
            )
        ),
        ui.column(
            6,
            ui.card(
                ui.card_header("检索结果"),
                detail_content,
                # 设置详细内容区域样式：添加内边距、最大高度和垂直滚动条
                style="padding: 20px; max-height: 800px; overflow-y: auto; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"
            )
        )
    )

def layout_6_6():
    """创建一个左右分栏的布局，用于动态输出内容。
    这个布局使用 output_ui 占位符，由服务器端渲染内容。
    """
    return ui.row(
        ui.column(
            6,
            ui.card(
                ui.card_header("WikiDocu"),
                ui.output_ui("main_output"),
                # 设置主输出区域样式：固定高度和垂直滚动条
                style="height: 500px; overflow-y: auto; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"
            )
        ),

        ui.column(
            6,
            ui.card(
                ui.card_header("检索结果"),
                ui.output_ui("detail_output"),
                # 设置详细输出区域样式：固定高度和垂直滚动条
                style="height: 500px; overflow-y: auto; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05);"
            )
        )
    )
