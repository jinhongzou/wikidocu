# config.py

from shiny import ui

# 配置字典，定义了不同类型的 navset 及其参数
# 当前只配置了 "navset_card_underline" 类型，用于创建带下划线的卡片式导航
navset_configs = {
    "navset_card_underline": {
        # "Respond" 是一个具体的 navset 实例配置
        # "title": "Respond" 设置了该 navset 的标题
        "Respond": {"title": "Respond"},
    },
}