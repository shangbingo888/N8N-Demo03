---
name: l2-database
level: L2
category: 数据处理与API集成
requires: [l2-data-transform]
feeds_into: [l3-rag, l3-business-orchestration]
---

# L2-07 数据库操作

## 概述

当 Google Sheets 不够用时，PostgreSQL、Supabase、BigQuery 等真正的数据库登场。在 AIGC_Files 中，Postgres 出现 50 次，Supabase 出现 2 次，BigQuery 出现 1 次。数据库常用于 AI 应用的持久化存储、向量数据的读写、以及企业级数据分析场景。

## 适用场景

- AI 处理结果持久化存储（替代 Google Sheets）
- 向量数据存储与查询（配合 RAG 系统）
- 企业数据仓库查询（BigQuery 分析）
- 用户数据/会话状态管理
- 批量 ETL 数据管道

## 核心节点

| 节点 | 用途 | 典型操作 |
|------|------|----------|
| `postgres` | PostgreSQL 读写 | SELECT/INSERT/UPDATE |
| `postgresTool` | AI Agent 工具化 | Agent 直接操作数据库 |
| `supabase` | Supabase (PG + Auth) | 全托管 PG 数据库 |
| `googleBigQuery` | 大数据分析查询 | SQL 查询 + 结果导出 |

## 输入定义

| 参数 | 说明 |
|------|------|
| Operation | `executeQuery` / `insert` / `update` / `delete` |
| Query / Table | SQL 语句或表名 |
| Columns | INSERT 时的列映射 |

## 输出定义

查询操作返回标准 JSON 数组：

```
[
  { "id": 1, "name": "...", "score": 0.95 },
  { "id": 2, "name": "...", "score": 0.82 }
]
```

## 节点组合模板

### AI 结果持久化

```
AI Agent (处理用户输入)
  → Set (映射为数据库字段)
  → Postgres (INSERT INTO results)
  → Respond to Webhook
```

### AI Agent 查询数据库（Agent 工具模式）

```
Telegram Trigger (用户询问数据)
  → AI Agent (解释查询意图)
    → PostgresTool (Agent 调用 SQL 查询)
  → Telegram (返回查询结果)
```

### ETL 数据管道

```
Schedule Trigger (定时)
  → HTTP Request (获取外部 API 数据)
  → Set (数据清洗与映射)
  → Postgres (UPSERT 到数据库)
```

## 参考工作流

| 文件 | 数据库使用模式 |
|------|--------------|
| `workflows/Postgres/0666_Postgres_Webhook_Create_Webhook.json` | Webhook → Postgres + OpenAI |
| `workflows/Webhook/1252_Webhook_Respondtowebhook_Automation_Webhook.json` | AI Agent + Postgres 查询 |
| `workflows/Filter/1414_Filter_Summarize_Automation_Triggered.json` | Notion → Supabase 向量存储 |
| `workflows/Googlebigquery/0806_Googlebigquery_Stickynote_Automate_Triggered.json` | BigQuery 数据分析 |

## 常见问题与经验

1. **连接安全**：数据库凭据通过 n8n Credentials 管理，支持 SSL 加密连接
2. **SQL 注入防护**：使用参数化查询（`$1, $2` 占位符），不要拼接用户输入到 SQL
3. **事务处理**：n8n 节点不支持跨节点事务，需要多步原子操作时在 Code 节点内完成
4. **连接池**：高频数据库操作可能耗尽连接池，用 Queue Mode 控制并发
5. **Google Sheets vs DB**：数据量 > 10000 行或需要复杂查询时，果断从 Sheets 迁移到 Postgres
6. **Supabase 生态**：Supabase 内置 Auth、Realtime、Vector Store，特别适合 AI 应用全栈开发

## 升级路径

- 向量存储 + AI 检索 → 学习 **[L3-05 RAG 检索增强生成]()**
- 多服务数据编排 → 学习 **[L3-08 业务全流程编排]()**
