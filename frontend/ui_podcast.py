"""
UI Components for Podcast-LLM

This module provides the UI components for the Podcast-LLM application using Shiny for Python.
"""

import os
from pathlib import Path
from shiny import ui

from .podcast_config import (
    DEFAULT_FAST_LLM_URL,
    DEFAULT_LONG_CONTEXT_LLM_URL,
    DEFAULT_TEXT_OUTPUT,
    DEFAULT_AUDIO_OUTPUT,
    DEFAULT_SOURCE_URL
)

# Create the main UI
ui_podcast = ui.page_fluid(
    # Custom CSS styling for centered layout
    ui.tags.style("""
        body {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            backdrop-filter: blur(10px);
        }
        
        .container-fluid {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h2 {
            color: #333333;
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        .card {
            background: rgba(255, 255, 255, 0.7);
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 25px;
            backdrop-filter: blur(10px);
        }
        
        .card-header {
            background: rgba(102, 126, 234, 0.2);
            color: #333333;
            border-radius: 14px 14px 0 0 !important;
            border-bottom: none;
            font-weight: 600;
            font-size: 1.2em;
            text-align: center;
            padding: 15px 20px;
        }
        
        .card-body {
            padding: 25px;
            background: transparent;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .control-label {
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
            display: block;
        }
        
        .form-control {
            border-radius: 8px;
            border: 2px solid rgba(225, 229, 233, 0.5);
            padding: 12px 15px;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.5);
        }
        
        .form-control:focus {
            border-color: rgba(102, 126, 234, 0.5);
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            background: rgba(255, 255, 255, 0.8);
        }
        
        .btn {
            border-radius: 8px;
            padding: 12px 25px;
            font-weight: 600;
            transition: all 0.3s ease;
            border: none;
        }
        
        .btn-primary {
            background: rgba(102, 126, 234, 0.3);
            color: #333333;
            border: 1px solid rgba(102, 126, 234, 0.3);
        }
        
        .btn-primary:hover {
            background: rgba(102, 126, 234, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }
        
        .btn-secondary {
            background: rgba(111, 122, 140, 0.3);
            color: #333333;
            border: 1px solid rgba(111, 122, 140, 0.3);
        }
        
        .btn-secondary:hover {
            background: rgba(111, 122, 140, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(74, 85, 104, 0.2);
        }
        
        .btn-lg {
            padding: 15px 30px;
            font-size: 1.1em;
        }
        
        .radio-inline, .checkbox-inline {
            margin-right: 20px;
            margin-bottom: 10px;
        }
        
        .radio label, .checkbox label {
            font-weight: 500;
            color: #555;
        }
        
        .shiny-text-output {
            background: rgba(248, 249, 250, 0.5);
            border-radius: 8px;
            border: 1px solid rgba(233, 236, 239, 0.5);
            padding: 15px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            height: 300px;
            overflow-y: auto;
            white-space: pre-wrap;
            backdrop-filter: blur(5px);
            /* Ensure the scrollbar is always visible */
            scrollbar-width: thin;
            scrollbar-color: rgba(102, 126, 234, 0.5) rgba(233, 236, 239, 0.5);
        }
        
        /* Webkit browsers scrollbar styling */
        .shiny-text-output::-webkit-scrollbar {
            width: 8px;
        }
        
        .shiny-text-output::-webkit-scrollbar-track {
            background: rgba(233, 236, 239, 0.5);
            border-radius: 4px;
        }
        
        .shiny-text-output::-webkit-scrollbar-thumb {
            background: rgba(102, 126, 234, 0.5);
            border-radius: 4px;
        }
        
        .shiny-text-output::-webkit-scrollbar-thumb:hover {
            background: rgba(102, 126, 234, 0.7);
        }
        
        .centered-content {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }
        
        .form-row {
            display: flex;
            flex-wrap: wrap;
            margin: 0 -10px;
        }
        
        .form-col {
            padding: 0 10px;
            flex: 1;
            min-width: 250px;
        }
        
        .action-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 20px;
        }
        
        .ml-3 {
            margin-left: 1rem !important;
        }
        
        .mb-4 {
            margin-bottom: 1.5rem !important;
        }
        
        .section-divider {
            text-align: center;
            color: rgba(102, 126, 234, 0.8);
            font-weight: 500;
            margin: 25px 0;
            font-size: 0.9em;
            letter-spacing: 1px;
        }
        
        @media (max-width: 768px) {
            .form-col {
                min-width: 100%;
                margin-bottom: 15px;
            }
            
            body {
                padding: 10px;
            }
        }
    """),
    
    ui.panel_title(ui.markdown(f"""### 欢迎使用 ***播客***""")),
    
    # Configuration Card
    ui.card(
        ui.card_header("配置信息"),
        ui.card_body(
            # Topic, Q&A Rounds, and Language
            ui.div(
                ui.div(
                    ui.div(
                        ui.div(
                            ui.div(
                                ui.input_text("topic", ui.HTML("<span style='color: red;'>播客主题*</span>"), placeholder="设定您的播客主题"),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),
                        ui.div(
                            ui.div(
                                ui.input_numeric("qa_rounds", "问答回合", value=2, min=1, max=3),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),
                        ui.div(
                            ui.div(
                                ui.input_radio_buttons("language", "语言", choices={"en": "EN", "zh": "中文"}, selected="zh"),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),
                        class_="form-row"
                    ),
                    class_="centered-content"
                ),
                
                # Operation Mode, Source Files and URLs in one row
                ui.div(
                    ui.div(
                        ui.div(
                            ui.div(
                                ui.input_radio_buttons("mode", "操作模式", 
                                                    choices={"research": "Research Mode (自动研究)", 
                                                            "context": "Context Mode (给定资料)"}, 
                                                    selected="context"),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),
                        ui.div(
                            ui.div(
                                ui.input_file("source_files", "资料文件", 
                                              placeholder ='dataset/news', multiple=True),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),
                        ui.div(
                            ui.div(
                                ui.input_text("source_urls", "资料链接",
                                            value="",
                                            placeholder="https://finance.sina.com.cn/wm/2024-02-03/doc-inaftiir0348604.shtml"),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),
                        class_="form-row"
                    ),
                    class_="centered-content"
                ),

                # LLM Base URLs
                ui.div(
                    ui.div("━━━━━━━━━━━━━━━━━━━━ 系统设置 ━━━━━━━━━━━━━━━━━━━━", 
                        class_="section-divider"),
                    ui.div(
                        ui.div(
                            ui.div(
                                ui.input_text("fast_llm_url", "Fast LLM Base URL", 
                                            value=DEFAULT_FAST_LLM_URL,
                                            placeholder="e.g., https://api.openai.com/v1"),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),
                        ui.div(
                            ui.div(
                                ui.input_text("long_context_llm_url", "Long Context LLM Base URL",
                                            value=DEFAULT_LONG_CONTEXT_LLM_URL,
                                            placeholder="e.g., https://api.openai.com/v1"),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),
                        class_="form-row"
                    ),
                    class_="centered-content"
                ),
                
                # Output Settings
                ui.div(
                    ui.div(
                        ui.div(
                            ui.div(
                                ui.input_text("text_output", ui.HTML("<span style='color: red;'>播客文案名称*</span>"), value=DEFAULT_TEXT_OUTPUT, placeholder="episode.md"),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),
                        ui.div(
                            ui.div(
                                ui.input_text("audio_output", "播客语音名称(可空)", value=DEFAULT_AUDIO_OUTPUT, placeholder="episode.mp3"),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),
                        ui.div(
                            ui.div(
                                ui.input_checkbox("use_checkpoints", "自动缓存", value=True),
                                class_="form-group"
                            ),
                            class_="form-col"
                        ),

                        class_="form-row"
                    ),
                    class_="centered-content"
                ),

                # LLM Settings and Custom Config
                # ui.div(
                #     ui.div(
                #         # ui.div(
                #         #     ui.div(
                #         #         ui.input_checkbox("use_checkpoints", "Enable Checkpoints", value=True),
                #         #         class_="form-group"
                #         #     ),
                #         #     class_="form-col"
                #         # ),
                #         # ui.div(
                #         #     ui.div(
                #         #         ui.input_file("custom_config", "Custom Config File (optional)", accept=[".yaml", ".yml"]),
                #         #         class_="form-group"
                #         #     ),
                #         #     class_="form-col"
                #         # ),
                #         # class_="form-row"
                #         ui.div(
                #             ui.div(
                #                 ui.input_action_button("audio_play", "Audio Play", class_="btn btn-primary ml-3"),
                #             ),
                #             class_="d-flex justify-content-center align-items-center"
                #         ),
                #         class_="form-row"
                #     ),
                #     class_="centered-content"
                # ),
                # Action buttons at the top
                ui.div(
                    ui.div(
                        ui.input_action_button("generate", "Generate Podcast", class_="btn btn-primary ml-3"),
                        #ui.input_action_button("stop_generation", "Stop Generation", class_="btn btn-primary ml-3"),
                        ui.input_action_button("audio_play", "Audio Play", class_="btn btn-danger ml-3"),
                        class_="d-flex justify-content-center align-items-center"
                    ),
                    class_="mb-4"
                ),
            )
        )
    ),
    
    # Action and Log Card
    ui.card(
        ui.card_header("日志追踪"),
        ui.card_body(
            # Log output below
            ui.div(
                ui.output_text_verbatim("log_output", placeholder=True),
                ui.tags.script("""
                    function scrollToBottom() {
                        var logOutput = document.querySelector('.shiny-text-output');
                        if (logOutput) {
                            logOutput.scrollTop = logOutput.scrollHeight;
                        }
                    }

                    function isScrolledToBottom(element) {
                        if (!element) return false;
                        return element.scrollTop + element.clientHeight >= element.scrollHeight - 5;
                    }
                    
                    // Force scroll to bottom with multiple attempts
                    function forceScrollToBottom() {
                        scrollToBottom();
                        // Additional attempts to ensure scrolling works
                        setTimeout(scrollToBottom, 50);
                        setTimeout(scrollToBottom, 100);
                        setTimeout(scrollToBottom, 200);
                    }
                    
                    // Create a MutationObserver to watch for changes
                    var observer = new MutationObserver(function(mutations) {
                        var logOutput = document.querySelector('.shiny-text-output');
                        if (logOutput) {
                            // Always scroll to bottom for new content
                            forceScrollToBottom();
                        }
                    });
                    
                    // Start observing once the element is available
                    function setupObserver() {
                        var logOutput = document.querySelector('.shiny-text-output');
                        if (logOutput) {
                            observer.observe(logOutput, {
                                childList: true,
                                characterData: true,
                                subtree: true
                            });
                            // Initial scroll to bottom
                            forceScrollToBottom();
                        }
                    }
                    
                    // Set up the observer when the page loads
                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', setupObserver);
                    } else {
                        setupObserver();
                    }
                    
                    // Also scroll to bottom on window load
                    window.addEventListener('load', function() {
                        forceScrollToBottom();
                    });
                    
                    // Scroll to bottom when Shiny outputs are updated
                    document.addEventListener('shiny:outputinvalidated', function(event) {
                        if (event.name === 'log_output') {
                            forceScrollToBottom();
                        }
                    });
                    
                    // Additional event listeners for more reliable scrolling
                    document.addEventListener('shiny:bound', function(event) {
                        if (event.bindingType === 'shiny.textOutput') {
                            forceScrollToBottom();
                        }
                    });
                    
                    // Handle manual scrolling - if user scrolls up, pause auto-scrolling
                    // until they scroll back down
                    var autoScroll = true;
                    var logOutput = null;
                    
                    document.addEventListener('DOMContentLoaded', function() {
                        logOutput = document.querySelector('.shiny-text-output');
                        if (logOutput) {
                            logOutput.addEventListener('scroll', function() {
                                // If user scrolls to bottom, re-enable auto-scroll
                                if (isScrolledToBottom(logOutput)) {
                                    autoScroll = true;
                                }
                            });
                        }
                    });
                    
                    // Additional scroll to bottom on focus
                    window.addEventListener('focus', function() {
                        forceScrollToBottom();
                    });
                """),
                class_="form-group log-container"
            )
        )
    )
)