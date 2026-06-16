---
name: l3-ai-text-gen
level: L3
category: AI多模型协作
requires: [l2-http-api, l2-data-transform]
feeds_into: [l3-ai-agent, l3-langchain, l3-rag, l3-multi-model]
---

# L3-01 AI 文本生成

## 概述

AI 文本生成是所有 AIGC 工作流的核心动力。在 AIGC_Files 集合中，OpenAI 节点出现 **573 次**（排名第二），涵盖 GPT-4/GPT-4o/GPT-4o-mini 系列模型。此外还包含 Gemini、DeepSeek、Mistral、Ollama 等模型的集成模式。

## 适用场景

- 文本摘要与翻译（新闻、反馈、会议记录）
- 内容创作（博客、SEO 文章、社交媒体帖子）
- 数据分类与情感分析
- 对话式 AI（客服机器人、学术助手）
- 代码生成与审查

## 模型选择指南

| 模型 | 推荐场景 | 典型配置 |
|------|----------|----------|
| GPT-4o | 复杂推理、多步骤任务 | 通用首选 |
| GPT-4o-mini | 简单分类、快速响应 | 成本敏感场景 |
| GPT-4.1 | 最新模型、高质量输出 | 高质量内容生成 |
| Gemini 2.0 Flash | 多模态理解、大数据量 | Google 生态集成 |
| DeepSeek V3/R1 | 推理与逻辑任务 | 中文优化、成本优势 |
| Ollama (本地) | 隐私敏感、离线场景 | 自托管 LLM |

## 节点组合模板

### 基础 AI 文本生成

```
[任意触发器]
  → OpenAI Chat Model (选择模型：gpt-4o-mini)
  → AI Agent (配置 System Prompt + 用户输入)
  → [输出节点]
```

### 多步 Prompt 工程

```
Webhook (用户主题)
  → AI Agent Step 1: 大纲生成 (GPT-4o)
    System: "你是一个 SEO 专家，为主题生成结构化大纲"
  → Code (提取大纲)
  → AI Agent Step 2: 逐节写作 (GPT-4o-mini)
    System: "根据大纲逐一撰写，每节 200-300 字"
  → Set (组装全文)
  → Respond to Webhook
```

### System Prompt 最佳实践

```
// 角色设定
"你是一个精通传统中文的 AI 新闻编辑"

// 任务说明
"你的任务：1. 从 {articles} 中选出 15 条最重要的 AI 技术新闻
 2. 翻译成准确的繁体中文，常用英文技术术语不翻译
 3. 每篇附带原文 URL
 4. 以 '早安，这是 yyyy/MM/dd 的 AI 新闻：' 开头"

// 输出格式约束
"仅输出最终摘要，不要附加任何解释"

// 引用数据
"articles: {{ $json.articles }}"
```

## 参考工作流

| 文件 | AI 文本模式 | 模型 |
|------|------------|------|
| `workflows/Telegram/Academic Assistant Chatbot (Telegram + OpenAI).json` | 简单对话 | OpenAI |
| `workflows/Manual/1543_Manual_Openai_Automation_Triggered.json` | GPT-4 反馈摘要 | GPT-4 |
| `workflows/Http/0970_HTTP_Schedule_Create_Webhook.json` | 新闻翻译摘要 | GPT-4.1 |
| `workflows/Http/1519_HTTP_Stickynote_Automation_Webhook.json` | DeepSeek 对话 | DeepSeek V3/R1 |
| `workflows/Stickynote/1379_Stickynote_Automation_Triggered.json` | 本地 LLM 对话 | Ollama |

## 常见问题与经验

1. **Token 限制**：不同模型有不同上下文窗口（GPT-4o: 128K, GPT-4o-mini: 128K），超长文本需分段处理
2. **温度参数**：创造性任务用较高 temperature（0.7-1.0），事实性任务用较低 temperature（0-0.3）
3. **成本控制**：GPT-4o 比 GPT-4o-mini 贵约 10-20 倍，简单任务优先用 mini
4. **Rate Limit 处理**：OpenAI 免费 Tier 有严格限流，加 `wait` 节点控制请求间隔
5. **中文 Prompt**：明确要求"繁体中文"或"简体中文"，否则模型可能输出混合语言
6. **Structured Output**：需要固定 JSON 格式输出时，使用 `outputParserStructured` 节点

## 升级路径

- 赋予工具调用能力 → 学习 **[L3-03 AI Agent 工具调用]()**
- 链式多步推理 → 学习 **[L3-04 LangChain 链式编排]()**
- 多模型比较 → 学习 **[L3-06 多模型协作与路由]()**
