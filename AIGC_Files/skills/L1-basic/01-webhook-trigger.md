---
name: l1-webhook-trigger
level: L1
category: 触发与响应
requires: []
feeds_into: [l1-schedule, l2-http-api, l3-ai-agent, l3-sub-workflow]
---

# L1-01 Webhook 触发与响应

## 概述

Webhook 是 n8n 中最通用的触发方式。通过暴露一个 HTTP 端点，任何外部服务都可以通过 POST 请求启动你的工作流。它是构建 API 驱动自动化、接收第三方回调（如 GitHub、Stripe、Shopify）的核心技能。

## 适用场景

- 接收外部系统的事件回调（GitHub webhook、支付回调、表单提交）
- 构建轻量级 API 端点，供前端或其他服务调用
- 作为 Telegram Bot / Discord Bot 的入口点
- 实时数据同步：当数据源发生变化时自动触发

## 输入定义

| 字段 | 类型 | 说明 |
|------|------|------|
| HTTP Method | `GET` / `POST` | 接收请求的方法 |
| Path | `string` | Webhook URL 路径 |
| Body | `JSON / Form / Raw` | 请求体，自动解析为 `$json` |
| Headers | `object` | 请求头信息，通过 `$json.headers` 访问 |
| Query Params | `object` | URL 查询参数 |

## 输出定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `$json` | `object` | 解析后的请求体 |
| `$json.headers` | `object` | 请求头信息 |
| `$json.query` | `object` | URL 查询参数 |
| `$json.params` | `object` | 路径参数 |

## 节点组合模板

### 基础 Webhook + 响应

```json
{
  "nodes": [
    {
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1.1,
      "name": "Webhook",
      "parameters": {
        "httpMethod": "POST",
        "path": "my-webhook",
        "options": {
          "responseMode": "responseNode"
        }
      }
    },
    {
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1.1,
      "name": "Respond to Webhook",
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ { \"status\": \"ok\", \"data\": $json } }}"
      }
    }
  ],
  "connections": {
    "Webhook": { "main": [[ { "node": "Respond to Webhook", "type": "main", "index": 0 } ]] }
  }
}
```

### Webhook + Slack 通知

```
Webhook → Set (格式化消息) → Slack (发送通知) → Respond to Webhook
```

## 参考工作流

| 文件 | 说明 |
|------|------|
| `workflows/Webhook/0834_Webhook_Slack_Create_Webhook.json` | Webhook 触发 → Slack 通知 |
| `workflows/Webhook/1694_Webhook_HTTP_Automation_Webhook.json` | Webhook → HTTP 请求 → 数据丰富 |
| `workflows/Webhook/1252_Webhook_Respondtowebhook_Automation_Webhook.json` | Webhook → AI Agent → Respond |
| `workflows/Webhook/1263_Webhook_Respondtowebhook_Automate_Webhook.json` | Webhook → Voice RAG Chatbot |

## 常见问题与经验

1. **认证安全**：生产环境中务必启用 Webhook 认证（Header Auth / Basic Auth），避免开放端点被滥用
2. **响应模式**：`responseMode` 推荐使用 `responseNode`，显式控制响应内容；如果响应在流程末尾，用 `lastNode`
3. **测试工具**：使用 `curl` 或 n8n 的 "Listen for Test Event" 功能调试
4. **超时配置**：长时间运行的工作流（>30s）考虑使用 `lastNode` 模式并调整 executionTimeout

## 升级路径

- 掌握本技能后 → 学习 **[L1-02 定时任务触发]()** 了解主动拉取模式
- 需要对接外部 API 时 → 学习 **[L2-01 HTTP API 调用与集成]()**
- 构建复杂业务 → 学习 **[L3-07 子工作流模块化]()** 将 Webhook 作为路由入口
