# components.py

from shiny import ui

def layout_box_bak(main_content, detail_content):
    return ui.row(
        ui.column(
            6,
            ui.card(
               #ui.card_header("WikiDocu"),
                main_content,  # 直接传内容
                style="height: 500px; overflow-y: auto;"
            )
        ),
        ui.column(
            6,
            ui.card(
                #ui.card_header("检索结果"),
                detail_content,  # 直接传内容
                style="height: 500px; overflow-y: auto;"
            )
        )
    )

def layout_box(main_content, detail_content):
    return ui.row(
        ui.column(
            6,
            ui.card(
                #ui.card_header("WikiDocu"),
                main_content,  # 直接传内容
                style="overflow-y: auto; max-height: 800px;"  # 改为 max-height
            )
        ),
        ui.column(
            6,
            ui.card(
                #ui.card_header("检索结果"),
                detail_content,  # 直接传内容
                style="overflow-y: auto; max-height: 800px;"  # 改为 max-height
            )
        )
    )
'''
app_ui = ui.page_fluid(
    layout_6_6(
        "这是主内容区域。",
        ui.markdown("## 这是右侧的 Markdown 内容")
    )
)
'''

def layout_6_6():
    return ui.row(
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
                ui.output_ui("detail_output"),  # Use selected value
                style="height: 500px; overflow-y: auto;"
            )
        )
    )
    # ui.row(
    #     ui.column(
    #         6,
    #         ui.card(
    #             ui.card_header("WikiDocu"),
    #             ui.output_ui("main_output"),  # 使用 output_ui 替代 output_markdown
    #             style="height: 500px; overflow-y: auto;"
    #         )
    #     ),
    #     ui.column(
    #         6,
    #         ui.card(
    #             ui.card_header("检索结果"),
    #             ui.output_ui("detail_output"),  # Use selected value
    #             style="height: 500px; overflow-y: auto;"
    #         )
    #     )
    # )
