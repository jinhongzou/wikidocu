
from shiny import App, ui, render, reactive

ui_wikidocu = ui.page_fluid(
    ui.tags.style("""
        /* ========== 隐藏模态框遮罩 ========== */
        .shiny-modal-backdrop {
            display: none !important;
        }
        
        /* ========== 动态内容区域 ========== */
        #dynamic_content {
            overflow: visible !important;
            min-height: auto;
            height: auto !important;
        }
        
        /* ========== 内容包装器：允许垂直滚动 ========== */
        .content-wrapper {
            background-color: rgba(255, 255, 255, 0); /* 完全透明 */
            overflow-y: auto;
            max-height: calc(100vh - 100px);
            width: 100%;

        }
        
        /* ========== 卡片 header：仅保留文字样式，去边框 ========== */
        .card-header {
            background-color: rgba(255, 255, 255, 0); /* 透明背景 */
            border-bottom: none;           /* 🔴 移除边框 */
            font-weight: bold;
            padding: 10px 15px;
            color: #000000;                /* 可选：设为白色文字 */

        }
        /* ========== 强制卡片宽度拉满 ========== */
        .card {
            width: 100% !important;
            max-width: 100% !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        /* ========== 卡片 body：完全透明，无边框、无阴影、无模糊 ========== */
        .card-body {
            background-color: rgba(255, 255, 255, 0); /* 透明背景 */
            border: none;                  /* 🔴 移除边框 */
            box-shadow: none;              /* 🔴 移除阴影 */
            padding: 15px;                 /* 保留内边距保证可读性 */
            
            width: 100% !important;
            max-width: 100% !important;
        }
    """),
    ui.panel_title(ui.markdown(f"""### 欢迎使用 ***WikiDocu***""")),
    #ui.markdown(f"""### 欢迎使用 ***WikiDocu***"""),

    # 用 div 包裹 dynamic_content 并添加 id 用于 JS 操作
    ui.div(
        ui.output_ui("dynamic_content"),
        class_="content-wrapper",
        style = "width: 100%; overflow: hidden;"
    ),

    # 页面底部自动滚动的 JavaScript 脚本
    ui.tags.script("""
        (function() {
            const observer = new MutationObserver(function() {
                const container = document.querySelector('.content-wrapper');
                if (container) {
                    container.scrollTop = container.scrollHeight;
                }
            });

            const target = document.querySelector('.content-wrapper');
            if (target) {
                observer.observe(target, { childList: true, subtree: true });
            }
        })();
    """)
)
