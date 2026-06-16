---
name: l1-schedule-trigger
level: L1
category: 触发与响应
requires: []
feeds_into: [l2-http-api, l2-google-sheets, l3-ai-text-gen, l3-business-orchestration]
---

# L1-02 定时任务触发

## 概述

Schedule Trigger 是主动式自动化的核心。它按你设定的时间规则定期触发工作流，无需外部事件驱动。结合 AI 能力后，可实现"每天早上 8 点总结 AI 新闻并推送到 Telegram"等自动化场景。

## 适用场景

- 定时数据同步（如每小时同步 Google Sheets 数据到数据库）
- 每日/每周报告生成与推送
- 定时爬取数据（RSS Feed、API 数据）
- 周期性 AI 任务（每日摘要、定时翻译）
- 监控告警（每分钟检查服务状态）

## 输入定义

| 字段 | 类型 | 说明 |
|------|------|------|
| Rule Type | `interval` / `cron` | 触发规则类型 |
| Interval | `hours` / `minutes` | 间隔触发（如每天 8 点） |
| Cron Expression | `string` | Cron 表达式（如 `0 8 * * *`） |

## 输出定义

| 字段 | 类型 | 说明 |
|------|------|------|
| `$json.timestamp` | `string` | 触发时的时间戳 |
| `$json` | `object` | 空对象，可作为流程起点 |

> 注意：Schedule Trigger 自身不携带业务数据，需要通过后续节点（HTTP Request、Google Sheets 等）获取实际数据。

## 节点组合模板

### 定时新闻摘要推送

```
Schedule Trigger (每天8:00)
  → HTTP Request (获取新闻 API 数据)
  → AI Agent (GPT-4 摘要翻译)
  → Telegram (发送消息)
```

### 定时数据同步

```
Schedule Trigger (每小时)
  → Google Sheets (读取数据)
  → Set (数据清洗)
  → Postgres (写入数据库)
```

### Cron 表达式参考

| 表达式 | 含义 |
|--------|------|
| `0 8 * * *` | 每天 8:00 |
| `0 */6 * * *` | 每 6 小时 |
| `0 9 * * 1` | 每周一 9:00 |
| `*/15 * * * *` | 每 15 分钟 |
| `0 0 1 * *` | 每月 1 日 0:00 |

## 参考工作流

| 文件 | 说明 |
|------|------|
| `workflows/Schedule/0486_Schedule_Telegram_Create_Scheduled.json` | 定时 → Telegram 发送 |
| `workflows/Schedule/1406_Schedule_Slack_Automation_Scheduled.json` | 定时会议摘要 → Slack |
| `workflows/Http/0970_HTTP_Schedule_Create_Webhook.json` | 每日 AI 新闻翻译摘要 |
| `workflows/Splitout/1934_Splitout_Schedule_Create_Scheduled.json` | 个性化 AI 技术新闻简报 |

## 常见问题与经验

1. **时区问题**：n8n 默认使用 UTC 时间，务必在 Settings 中将 Timezone 设为 `Asia/Shanghai` 或目标时区
2. **幂等性**：定时任务可能重复执行，关键操作（如写入数据库）应做好去重或幂等处理
3. **Cron vs Interval**：简单间隔用 Interval 模式，复杂调度用 Cron 表达式
4. **资源消耗**：高频定时任务（<5分钟）会增加 n8n 执行负载，建议合并或降低频率

## 升级路径

- 整合数据获取 → 学习 **[L2-01 HTTP API 调用与集成]()**
- 定时生成 AI 内容 → 学习 **[L3-01 AI 文本生成]()**
- 构建完整日报系统 → 学习 **[L3-08 业务全流程编排]()**
