# components.py

from shiny import ui

def left_panel():
    return ui.div("左侧内容", style="border:1px solid #ccc; padding:10px;")

def right_panel():
    return ui.div("右侧内容", style="border:1px solid #ccc; padding:10px;")

# def layout_6_6():
#     return ui.row(
#         ui.column(6, left_panel()),
#         ui.column(6, right_panel())
#     )# components.py

def layout_6_6():
    return ui.row(
        ui.column(6, ui.output_text("detail_output", inline=False)),
        ui.column(6, ui.output_text("main_output", inline=False))
    )