# navset_builder.py

from typing import List
from shiny import ui
from .config import navset_configs
from .components import layout_6_6,layout_box

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
            nav_panels = []
            panel_id = f"{navset_type}"

            body_content = layout_6_6()
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
            #ui.h4(f"{navset_type} - {navset_id}"),
            component,
            style="margin-bottom: 2rem; padding: 1.5rem; background-color: rgba(135, 206, 250, 0.5); border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 0 2px 5px rgba(0,0,0,0.05); backdrop-filter: blur(2px);"
        ))
        return components


    def create_navset_ui_from_context(self, navset_type: str, main_content : str, detail_content: str) -> List:
        """根据提供的内容动态创建 navset 组件的 UI。
        此方法用于将主内容和详细内容（如检索结果）填充到预定义的布局中。
        """
        navset_function = getattr(ui, navset_type)
        components = []

        # 遍历配置字典中指定类型的 navset 配置
        for navset_id, params in self.navset_configs[navset_type].items():
            navset_kwargs = params.copy()

            # 创建导航面板列表
            nav_panels = []
            # 使用 navset_type 作为面板 ID
            panel_id = f"{navset_type}"

            # 使用 layout_box 函数创建包含主内容和详细内容的布局
            body_content = layout_box(main_content, detail_content)
            
            # 将布局添加到导航面板中
            nav_panels.append(
                ui.nav_panel(panel_id, body_content, value=panel_id)
            )

            # 使用 Shiny 的 navset 函数创建最终的导航组件
            component = navset_function(
                *nav_panels,
                id=f"{navset_type}_{navset_id}",
                **navset_kwargs
            )

            # 将组件包装在 div 中并添加样式，然后添加到组件列表
            # 样式包括：底部外边距、内边距、背景色、圆角边框、边框和阴影
            components.append(ui.div(
                #ui.h4(f"{navset_type} - {navset_id}"),
                #ui.h4(f"{navset_id}"),
                component,
                style="margin-bottom: 2rem; padding: 1.5rem; background-color: #ffffff; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"
            ))

        return components



layout_box