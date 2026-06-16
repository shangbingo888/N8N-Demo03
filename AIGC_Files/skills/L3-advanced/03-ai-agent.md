---
name: l3-ai-agent
level: L3
category: AI多模型协作
requires: [l3-ai-text-gen, l2-http-api, l2-database]
feeds_into: [l3-multi-model, l3-sub-workflow, l3-business-orchestration]
---

# L3-03 AI Agent 工具调用

## 概述

AI Agent 是 n8n 中最高级的 AI 模式。不同于简单的"输入→AI→输出"，Agent 可以自主决定使用什么工具、以什么顺序执行、何时完成任务。在 AIGC_Files 中，Agent 节点出现 **368 次**（排名第三），GmailTool 出现 199 次，GoogleCalendarTool 出现 147 次。

## 适用场景

- 智能客服：自动查询订单、处理退款、搜索知识库
- 日历助手：查询日程、创建会议、发送邀请
- 邮件处理：分类、摘要、自动回复
- 数据分析：自然语言查询数据库
- 多工具编排：根据用户意图自动调用不同服务

## Agent 架构

```
AI Agent
  ├─ LLM Model (GPT-4o / Gemini / DeepSeek)
  ├─ System Prompt (角色与行为约束)
  ├─ Memory (会话上下文)
  └─ Tools (Agent 可调用的工具列表)
       ├─ HTTP Request Tool (调用外部 API)
       ├─ Gmail Tool (发送/查询邮件)
       ├─ Google Calendar Tool (日程管理)
       ├─ Google Sheets Tool (读写数据)
       ├─ Postgres Tool (数据库查询)
       ├─ Workflow Tool (调用子工作流)
       └─ MCP Client Tool (MCP 服务调用)
```

## 节点组合模板

### 邮件处理 Agent

```
Gmail Trigger (收到新邮件)
  → AI Agent (OpenAI GPT-4o)
    System: "你是邮件处理助手，根据邮件内容决定：分类、回复、标记重要、转发"
    Tools:
      - Gmail Tool (发送/回复/标记邮件)
      - Google Sheets Tool (记录统计数据)
      - HTTP Request Tool (查询外部信息)
  → Gmail / Sheets (Agent 自主调用)
```

### 日历管理 Agent

```
Telegram Trigger (用户说"安排下周一的会议")
  → AI Agent (GPT-4o)
    System: "你是日历助手，帮助用户管理日程"
    Tools:
      - Google Calendar Tool (查询/创建/修改日程)
  → Telegram (返回操作结果)
```

### MCP 工具集成

```
Webhook (用户请求)
  → MCP Client (连接外部 MCP Server)
  → AI Agent
    Tools:
      - MCP Client Tool (调用 MCP Server 提供的工具)
```

### 搜索任务拆分 + 执行模式

这是从播客生成管道中提取的高级 Agent 模式，使用 Structured Output Parser 约束输出格式：

```
阶段 1 - 任务拆分:
  Agent (搜索任务拆分)
    Model: DeepSeek Chat Model
    Output Parser: Structured Output Parser
      Schema: { "rationale": "", "query": [""] }
    Prompt: "生成多样化搜索查询，最多 N 个"
  → Split Out (按 query 字段拆分)

阶段 2 - 逐条执行:
  Loop Over Items
    → Agent (搜索任务执行)
      Model: DeepSeek Chat Model
      Tools: SerpAPI (网络搜索)
      Output Parser: Structured Output Parser
        Schema: { "summary": "" }
      Prompt: "搜索并总结，如结果不满足则换关键词继续，最多 N 轮"
  → 数据整理 (Code: 合并所有摘要)

阶段 3 - 内容生成:
  Agent (播客脚本制作)
    Model: DeepSeek Chat Model
    Output Parser: Structured Output Parser
      Schema: { "result": [{"text": "", "type": "man/women"}] }
    Prompt: "基于搜索资料编写播客对话脚本"
  → Split Out → 逐条 TTS → Audio Merge
```

**Structured Output Parser 关键配置**：
- `jsonSchemaExample`: 定义 JSON 输出格式模板
- Agent 节点的 `hasOutputParser: true` 确保输出符合 Schema
- 结合 `retryOnFail: true, maxTries: 5` 处理解析失败

## 参考工作流

| 文件 | Agent 模式 | 工具集 |
|------|-----------|--------|
| `workflows/Gmailtool/0677_Gmailtool_Splitout_Create_Webhook.json` | 邮件 Agent | Gmail + SplitOut |
| `workflows/Googlecalendartool/1247_Googlecalendartool_Stickynote_Automation_Triggered.json` | 日历 Agent | Google Calendar |
| `workflows/Stickynote/1703_Stickynote_Webhook_Automation_Webhook.json` | 旅行规划 Agent | Couchbase + Gemini + OpenAI |
| `workflows/Woocommercetool/1599_Woocommercetool_Manual_Automation_Webhook.json` | 购物助手 Agent | WooCommerce + RAG |
| **`Workflow/workflow.json`** | **搜索→摘要→播客 Agent 管道** | **SerpAPI + Structured Output Parser** |
| **`Workflow/current_state.json`** | **Webhook → DeepSeek Agent → Mimo TTS** | **DeepSeek Chat Model** |
| **`Workflow/WorkflowDemo01/主工作流_docker_.json`** | **AI 创作 Agent × 4（角色/分镜/配音/字幕）** | **DeepSeek + Structured Output Parser** |

## 常见问题与经验

1. **Tool 描述至关重要**：Agent 根据 Tool 的 name 和 description 决定何时使用，写得越清晰准确越好
2. **工具数量控制**：过少无法完成任务，过多会让 Agent 困惑。一般 3-8 个工具为佳
3. **错误回退**：Agent 调用工具失败时，需要在 System Prompt 中定义回退策略
4. **Token 消耗**：每次 Agent 决策都需要将完整的对话历史 + 工具列表发送给 LLM，长期会话 Token 消耗大
5. **Memory 管理**：使用 Memory Buffer Window 节点限制上下文长度（如保留最近 10 轮对话）
6. **安全边界**：Agent 可能调用危险操作（删除数据、发送邮件），通过 Tool 的权限限制降低风险

## 升级路径

- 复杂多步推理 → 学习 **[L3-04 LangChain 链式编排]()**
- 工具封装为子工作流 → 学习 **[L3-07 子工作流模块化]()**
- 多 Agent 协作 → 学习 **[L3-08 业务全流程编排]()**
