# Podcast-LLM

Podcast-LLM 是一个自动化播客生成系统，结合大语言模型（LLM）与文本转语音（TTS）技术，能够创建高质量、富有吸引力的播客节目。该系统支持从单一主题出发，通过自动研究和内容生成完整的播客剧集；同时也可利用现有的文档、文章、网页、视频或音频等资料作为输入，自动生成结构化的对话式内容。

---

## 功能特性

- **自动研究**：通过维基百科和网络搜索自动收集主题背景信息。
- **多源内容提取**：支持 PDF、Word 文档、网页文章、YouTube 视频及音频文件等多种输入格式。
- **自然对话生成**：模拟主持人与嘉宾之间的问答式对谈，增强节目真实感。
- **多模型支持**：兼容 OpenAI、Google、Anthropic 等主流 LLM 提供商，并支持兼容 OpenAI 协议的第三方模型（如魔塔）。
- **文本转语音（TTS）**：集成 Google Cloud TTS 与 ElevenLabs，实现高质量语音合成。
- **检查点机制**：保存各阶段中间结果，便于流程恢复与调试。
- **图形界面（GUI）**：基于 Gradio 提供直观易用的网页操作界面。
- **命令行接口（CLI）**：支持脚本化调用，便于自动化集成。

---

## 系统架构

系统由核心生成模块与辅助支持模块构成，结构清晰、可扩展性强。

### 核心生成流程

| 模块 | 文件 | 功能 |
|------|------|------|
| 研究模块 | `research.py` | 从维基百科和网络搜索中获取背景资料 |
| 大纲模块 | `outline.py` | 构建章节化的内容结构 |
| 撰写模块 | `writer.py` | 生成自然流畅的对话脚本 |
| TTS 模块 | `text_to_speech.py` | 将脚本转换为音频文件 |
| 控制器 | `generate.py` | 协调整个生成流程 |

### 支持模块

- **配置管理** (`config/`)：统一管理 API 密钥与系统参数。
- **内容提取器** (`extractors/`)：处理不同类型的源文件。
- **工具库** (`utils/`)：提供嵌入、LLM 封装、速率限制等功能。
- **数据模型** (`models.py`)：使用 Pydantic 定义结构化数据类型。
- **GUI 界面** (`gui.py`)：提供可视化操作入口。

---

## 安装指南

1. **克隆项目仓库**：
   ```bash
   git clone <repository-url>
   cd podcast-llm
   ```

2. **安装依赖包**：
   ```bash
   pip install -r requirements.txt
   ```

3. **配置 API 密钥**：在 `.env` 文件中填写所需密钥：
   ```env
   OPENAI_API_KEY=your-openai-api-key
   TAVILY_API_KEY=your-tavily-api-key
   GOOGLE_API_KEY=your-google-api-key
   ELEVENLABS_API_KEY=your-elevenlabs-api-key
   ANTHROPIC_API_KEY=your-anthropic-api-key
   ```

4. **调整系统设置**：根据需要修改 `config/config.yaml` 中的参数。

---

## 使用方法

### 命令行模式（CLI）

#### 使用自动研究生成播客
```bash
python -m podcast_llm.generate "人工智能" --mode research --qa-rounds 2 --language zh
```

#### 基于现有资料生成播客
```bash
python -m podcast_llm.generate "机器学习" --mode context --sources document.pdf https://example.com/article --language en
```

#### 生成带音频输出的播客
```bash
python -m podcast_llm.generate "量子计算" --mode research --audio-output episode.mp3 --language zh
```

#### 使用兼容 OpenAI 协议的模型（如魔塔）

使用以下参数进行测试：
- `api_key`: `sk-xxx`
- `tts model_name`: `qwen-tts`
- `llm model_name`: `qwen3-coder-plus`
- `sources`: `news.txt`

执行命令：
```bash
python -m podcast_llm.generate "人工智能" \
  --mode context \
  --sources news.txt \
  --fast-llm-base-url "https://dashscope.aliyuncs.com/compatible-mode/v1" \
  --long-context-llm-base-url "https://dashscope.aliyuncs.com/compatible-mode/v1" \
  --text-output "./episode.txt" \
  --language zh
```

#### 基于网页内容生成播客
```bash
python -m podcast_llm.generate "加强商业银行互联网助贷业务管理" \
  --language zh \
  --mode context \
  --sources https://www.gov.cn/zhengce/202504/content_7017143.htm \
  --fast-llm-base-url "https://dashscope.aliyuncs.com/compatible-mode/v1" \
  --long-context-llm-base-url "https://dashscope.aliyuncs.com/compatible-mode/v1" \
  --text-output "./episode.txt" \
  --audio-output "./episode.mp3"
```

```bash
 python -m podcast_llm.generate "金融监管总局修改三个办法" --mode context   --sources https://www.sg.gov.cn/jrgzj/gzdt/content/post_2582635.html   --fast-llm-base-url "https://dashscope.aliyuncs.com/compatible-mode/v1"   --long-context-llm-base-url "https://dashscope.aliyuncs.com/compatible-mode/v1"  --text-output "./episode.txt" --audio-output "./episode2.mp3" --language zh
```

 python -m podcast_llm.generate "金融监管总局修订发布三个办法" --mode context   --sources D:\github_rep\WikiDocu\wikidocu\podcast_llm\三个办法.txt   --fast-llm-base-url "https://dashscope.aliyuncs.com/compatible-mode/v1"   --long-context-llm-base-url "https://dashscope.aliyuncs.com/compatible-mode/v1"  --text-output "./episode.txt"  --language zh --audio-output "./episode.mp3"  --audio-play True



### 图形用户界面（GUI）

启动 Web 界面：
```bash
python -m podcast_llm.gui
```

GUI 支持以下功能：
- 设置播客主题与语言
- 选择“研究模式”或“上下文模式”
- 上传本地文件或输入网页链接
- 配置 LLM 与 TTS 参数
- 指定输出路径（文本与音频）
- 实时查看日志与进度
- 自定义 `base_url`（用于魔塔等兼容 OpenAI 协议的模型）

---

## FFmpeg 安装说明

为确保音频处理正常运行，请预先安装 FFmpeg。

### Windows 安装步骤：
1. 访问 [FFmpeg 官网下载页](https://ffmpeg.org/download.html)
2. 下载适用于 Windows 的静态构建版本
3. 解压至指定目录（例如：`C:\ffmpeg`）
4. 将 `C:\ffmpeg\bin` 添加到系统环境变量 `PATH`
5. 重启终端并验证安装：
   ```bash
   ffmpeg -version
   ```
   若正确显示版本信息，则安装成功。

> 参考教程：[知乎文章 - 如何安装 FFmpeg（Windows 版）](https://zhuanlan.zhihu.com/p/692019886)

---

## 兼容 OpenAI 协议的模型支持（如魔塔）

Podcast-LLM 支持使用遵循 OpenAI 接口规范的第三方模型服务（如阿里云魔塔平台的 Qwen 系列模型）。使用方法如下：

1. 在调用时指定自定义 `base_url`
2. 使用 `.env` 中的 `OPENAI_API_KEY` 提供认证密钥

示例代码：
```python
from podcast_llm.utils.llm import get_fast_llm, get_long_context_llm
from podcast_llm.config import PodcastConfig

config = PodcastConfig.load('config/config.yaml')

# 使用魔塔的 Qwen 模型
fast_llm = get_fast_llm(config, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
long_context_llm = get_long_context_llm(config, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
```

您也可以通过环境变量等方式进一步简化配置。

---

## 数据模型（Pydantic）

系统使用 Pydantic 进行结构化数据建模，贯穿整个生成流程：

- `PodcastOutline`：播客整体结构
- `PodcastSection` / `PodcastSubsection`：分层内容组织
- `Script` / `ScriptLine`：包含说话人角色的完整脚本
- `Question` / `Answer`：单轮对话单元
- `WikipediaPages` / `SearchQueries`：研究阶段的数据结构

---

## 提示词系统（Prompts）

### 1. LangChain Hub 提示词

系统默认从 LangChain Hub 加载以下提示词模板：
- `evandempsey/podcast_wikipedia_suggestions:58c92df4` —— 推荐维基百科文章
- `evandempsey/podcast_research_queries:561acf5f` —— 生成搜索关键词
- `evandempsey/podcast_interviewer_role:bc03af97` —— 主持人角色设定
- `evandempsey/podcast_interviewee_role:0832c140` —— 嘉宾角色设定
- `evandempsey/podcast_rewriter:181421e2` —— 脚本润色
- `evandempsey/podcast_outline:6ceaa688` —— 生成节目大纲

### 2. 本地提示词支持

为降低对外部依赖，系统支持将提示词下载至本地使用：

- 执行脚本：
  ```bash
  python download_prompts.py
  ```

- 生成目录：`local_prompts/`，包含如下 JSON 文件：
  - `podcast_outline.json`
  - `podcast_wikipedia_suggestions.json`
  - `podcast_research_queries.json`
  - `podcast_interviewer_role.json`
  - `podcast_interviewee_role.json`
  - `podcast_rewriter.json`
  - `prompts_summary.json`
  - `README.md`（说明文档）

- 加载逻辑：优先读取本地提示词，若不存在则回退至 LangChain Hub。

### 3. 配置文件中的模板

在 `config/config.yaml` 中定义了播客的开场白与结束语模板：
```yaml
intro: "Welcome to {podcast_name}. Today we've invited an expert to talk about {topic}."
outro: "That's all for today. Thank you for listening to {podcast_name}. See you next time when we'll talk about whatever you want."
```

同时可自定义 `episode_structure`（剧集结构模板）。

### 4. 提示词动态修改

在 `outline.py` 中，系统会自动向原始提示词添加 JSON 输出格式要求，确保结构化响应。

### 5. 中文语境适配

所有对话类提示词均已修改为**中文输出**。在以下文件中新增语境指令：

```text
TONE:
- 使用中文进行所有对话
- 语气自然，如同在 IRC 或 Reddit 上交流
- 注意语法正确、标点规范
```

文件包括：
- `podcast_interviewer_role.json`
- `podcast_interviewee_role.json`
- `podcast_rewriter.json`

自定义提示词时，请保持中文语境的一致性。

---

## 内容提取支持

系统支持从多种来源提取文本内容：

| 来源类型 | 技术实现 |
|--------|---------|
| PDF 文件 | PyPDFLoader |
| Word 文档 | python-docx |
| 网页文章 | newspaper3k |
| YouTube 视频 | YouTubeTranscriptApi |
| 音频文件 | OpenAI Whisper 转录 |
| 纯文本/Markdown | 直接读取 |

---

## 核心技术栈

- **LangChain**：LLM 调用与提示词管理
- **OpenAI API / 兼容模型**（如魔塔）：核心语言模型与嵌入服务
- **Google Generative AI**：替代 LLM 提供商
- **Anthropic Claude**：高阶推理模型支持
- **Google Cloud TTS / ElevenLabs**：高质量语音合成
- **Tavily**：网络搜索与信息检索
- **Gradio**：构建交互式 Web 界面
- **Pydantic**：数据验证与序列化

---

## 工作流程

1. **研究阶段**
   - 推荐相关维基百科条目
   - 获取维基内容
   - 生成补充搜索关键词
   - 执行网络搜索并抓取结果

2. **大纲生成**
   - 利用 LLM 构建逻辑清晰的章节结构
   - 支持多级子章节划分

3. **脚本撰写**
   - 模拟主持人与专家问答生成初稿
   - 重写优化语言流畅度与自然性
   - 插入开场白与结束语

4. **音频生成**
   - 使用 TTS 将每段脚本转为语音
   - 为不同角色分配不同音色
   - 合成完整播客音频文件

---

## 检查点机制

系统在关键节点自动保存中间结果，包括：
- 背景研究数据
- 生成的大纲
- 草稿脚本
- 最终脚本

优势：
- 支持中断后继续生成
- 便于调试特定阶段
- 避免重复调用 API

---

## 速率限制与错误处理

- **速率控制**：防止超出各 API 提供商的调用配额
- **指数退避重试**：提升网络请求稳定性
- **全面日志记录**：便于排查问题
- **优雅降级**：当非关键组件失败时仍能继续运行

---

## 贡献指南

欢迎贡献！您可以通过以下方式参与项目：
- 提交 Pull Request
- 报告 Bug 或提出功能建议（Issue）
- 优化提示词或翻译文档

---

## 许可证

[请在此处填写您的开源许可证名称，例如 MIT License]