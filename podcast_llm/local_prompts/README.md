# 本地提示词使用说明

## 概述

本项目支持从LangChain Hub下载提示词并在本地使用，以减少对外部服务的依赖并提高加载速度。系统支持中英文双语提示词。

## 下载提示词

运行以下脚本可将所有提示词下载到本地：

```bash
python download_prompts.py
```

这将在`local_prompts/`目录下创建以下JSON文件：
- `podcast_outline.json` - 用于生成播客大纲（英文）
- `podcast_outline_zh.json` - 用于生成播客大纲（中文）
- `podcast_wikipedia_suggestions.json` - 用于建议维基百科文章（英文）
- `podcast_wikipedia_suggestions_zh.json` - 用于建议维基百科文章（中文）
- `podcast_research_queries.json` - 用于生成研究查询（英文）
- `podcast_research_queries_zh.json` - 用于生成研究查询（中文）
- `podcast_interviewer_role.json` - 用于面试者角色（英文）
- `podcast_interviewer_role_zh.json` - 用于面试者角色（中文）
- `podcast_interviewee_role.json` - 用于受访者角色（英文）
- `podcast_interviewee_role_zh.json` - 用于受访者角色（中文）
- `podcast_rewriter.json` - 用于重写脚本（英文）
- `podcast_rewriter_zh.json` - 用于重写脚本（中文）
- `prompts_summary.json` - 英文提示词摘要文件
- `prompts_summary_zh.json` - 中文提示词摘要文件

## 使用本地提示词

代码会自动优先尝试从本地加载提示词，如果本地文件不存在则会从LangChain Hub获取。

## 提示词结构

每个JSON文件包含以下结构：
- `id`: 提示词在Hub上的ID
- `messages`: 提示词的消息列表
  - `index`: 消息索引
  - `template`: 消息模板
  - `type`: 消息类型

## 自定义提示词

要自定义提示词，可以直接编辑`local_prompts/`目录下的JSON文件。修改后，系统会自动使用您的本地版本而不是从Hub获取。

## 语言选择

系统支持通过`--language`参数选择提示词语言：
- `--language en` 使用英文提示词（默认）
- `--language zh` 使用中文提示词

在GUI界面中也有相应的语言选择选项。

## 注意事项

### 对话语境要求

所有提示词中的对话语境都已修改为使用**中文**。我们已经更新了以下提示词以明确要求使用中文：

1. `podcast_interviewer_role.json` - 面试者角色提示词
2. `podcast_interviewee_role.json` - 受访者角色提示词
3. `podcast_rewriter.json` - 脚本重写提示词

在这些提示词中，我们都添加了以下语境要求：
```
TONE:
- Use Chinese for all conversation.
- Speak informally, as if writing on IRC or Reddit.
- Use good grammar and punctuation.
```

### 中文语境要求说明

在自定义提示词时，请保持以下语境要求：
1. 使用中文进行对话
2. 保持自然、口语化的表达方式
3. 符合中文播客的表达习惯
4. 保持采访者和受访者之间的自然互动

### 示例修改

如果需要进一步自定义提示词，请确保在TONE部分保持中文语境要求：
```
TONE: 
- Use Chinese for all conversation.
- 使用中文进行对话
- 以口语化的方式表达，就像在聊天室或论坛上交流一样
- 使用良好的语法和标点符号
```