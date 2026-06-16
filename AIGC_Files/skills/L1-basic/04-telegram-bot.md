---
name: l1-telegram-bot
level: L1
category: 触发与响应
requires: []
feeds_into: [l2-http-api, l3-ai-text-gen, l3-ai-agent, l3-rag]
---

# L1-04 Telegram Bot 对话

## 概述

Telegram 是 n8n 中最流行的即时通讯集成。通过 Telegram Trigger 接收用户消息，处理后通过 Telegram Send 节点回复。搭配 AI 模型后可快速构建智能聊天机器人——这也是 AIGC_Files 集合中出现频率最高的完整应用模式之一。

## 适用场景

- AI 聊天机器人（学术助手、客服、问答）
- 内容推送通知（新闻、报告、告警）
- 交互式工具（输入 URL 返回摘要、输入关键词返回图片）
- 团队协作自动化（通过 Bot 触发工作流）

## 输入定义

| 字段 | 来源 | 说明 |
|------|------|------|
| `message.text` | `$json.message.text` | 用户发送的消息文本 |
| `message.chat.id` | `$json.message.chat.id` | 会话 ID（用于回复） |
| `message.from` | `$json.message.from` | 发送者信息 |
| `message.photo` | `$json.message.photo` | 发送的图片（如有） |

## 输出定义

发送消息的核心参数：

| 参数 | 类型 | 说明 |
|------|------|------|
| `chatId` | `string` | 目标会话 ID（通常用表达式） |
| `text` | `string` | 发送的文本内容 |
| `additionalFields.appendAttribution` | `boolean` | 是否添加 "via n8n" 署名 |

## 节点组合模板

### 最简 AI 聊天机器人（5 节点）

```
Telegram Trigger (监听消息)
  → OpenAI Chat Model (设置模型)
  → AI Agent (带 System Prompt)
  → Telegram Send (回复用户)
  + Error Handler (stopAndError)
```

**核心表达式**：
```
// Telegram Trigger → AI Agent 的 prompt
={{ $('Telegram Trigger').item.json.message.text }}

// AI Agent → Telegram Send 的 chatId
={{ $('Telegram Trigger').item.json.message.chat.id }}

// AI Agent → Telegram Send 的 text
={{ $('Academic Assistant AI Agent').item.json.output }}
```

### 多步骤 Bot（含数据获取）

```
Telegram Trigger
  → Switch (根据消息内容分支)
    ├─ 分支1: HTTP Request (获取外部数据) → AI Agent → Telegram
    ├─ 分支2: Google Sheets (查询数据) → Telegram
    └─ 默认: AI Agent (通用对话) → Telegram
```

## 参考工作流

| 文件 | 说明 |
|------|------|
| `workflows/Telegram/Academic Assistant Chatbot (Telegram + OpenAI).json` | 学术助手 Bot（最简模式） |
| `workflows/Telegram/1533_Telegram_Splitout_Automation_Webhook.json` | YouTube 视频摘要 Bot |
| `workflows/Telegram/1341_Telegram_Splitout_Automate_Webhook.json` | 自动化研究报告生成 |
| `workflows/Telegram/1975_Telegram_Googledocs_Automation_Webhook.json` | DeepSeek AI Agent + 长期记忆 |

## 常见问题与经验

1. **Bot Token**：通过 BotFather (@BotFather) 创建 Bot 获取 Token，在 n8n 中配置 Telegram 凭据
2. **Webhook URL**：Telegram Trigger 需要公网可达的 URL，开发环境用 ngrok 或 n8n cloud
3. **消息格式**：Telegram 支持 Markdown/HTML 格式，在 `additionalFields` 中设置 `parse_mode`
4. **长回复**：如果 AI 回复过长（>4096 字符），需要分段发送或使用 `splitOut`
5. **按键交互**：Telegram 支持 Inline Keyboard，可实现按钮式交互体验
6. **并发处理**：多人同时对话时，`chatId` 确保消息路由到正确用户

## 升级路径

- 接入 AI 对话能力 → 学习 **[L3-01 AI 文本生成]()**
- 赋予工具调用能力 → 学习 **[L3-03 AI Agent 工具调用]()**
- 增加文档问答 → 学习 **[L3-05 RAG 检索增强生成]()**
- 多 Bot 协作 → 学习 **[L3-07 子工作流模块化]()**
