# navset_builder.py

from typing import List
from shiny import ui
from config import navset_configs
from components import layout_6_6


class NavsetUIBuilder:
    def __init__(self, navset_configs):
        self.navset_configs = navset_configs

    def create_navset_ui(self, navset_type: str) -> List:
        """动态创建 navset 组件的 UI"""
        navset_function = getattr(ui, navset_type)
        components = []

        for navset_id, params in self.navset_configs[navset_type].items():
            navset_kwargs = params.copy()

            # 创建导航面板
            page_fluid = []
            panel_id = f"{navset_type}_1"

            body_content = layout_6_6()
            page_fluid.append(
                ui.page_fluid(panel_id, body_content, value=panel_id)
            )

            # 创建 navset 组件
            component = navset_function(
                *page_fluid,
                id=f"{navset_type}_{navset_id}",
                **navset_kwargs
            )

            components.append(ui.div(
                ui.h4(f"{navset_type} - {navset_id}"),
                component,
                style="margin-bottom: 2rem;"
            ))

        return components