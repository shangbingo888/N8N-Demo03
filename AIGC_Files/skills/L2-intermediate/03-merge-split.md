---
name: l2-merge-split
level: L2
category: 数据处理与API集成
requires: [l2-http-api, l2-data-transform]
feeds_into: [l2-condition-filter, l3-ai-text-gen, l3-multi-model]
---

# L2-03 数据合并与分流

## 概述

当工作流从多个数据源获取数据，或需要对大量数据进行批量处理时，Merge、SplitOut、SplitInBatches 成为关键的能力。在 AIGC_Files 集合中，SplitOut 出现了 **286 次**，SplitInBatches 出现了 **222 次**，是最高频的数据流控制节点。

## 适用场景

- 合并两个 API 的数据为统一格式
- 将列表数据逐条处理（如逐行 AI 分析）
- 按条件将数据分流到不同处理管道
- 限制处理数量（取 Top N）

## 核心节点速览

| 节点 | 功能 | 使用场景 |
|------|------|----------|
| `merge` | 合并多个输入源 | 双源数据聚合 |
| `splitOut` | 将数组拆分为独立 items | 逐项处理 |
| `splitInBatches` | 按批次拆分 | 大数据量分批 |
| `aggregate` | 聚合多 items 为单个 | 汇总结果 |
| `limit` | 限制通过的数据量 | 取前 N 条 |
| `itemLists` | 列表操作（拼接、排序） | 结果组装 |

## 节点组合模板

### 双源合并 + AI 处理

```
HTTP Request (NewsAPI)
  → Set (标准化为 { articles, source: "newsapi" })

HTTP Request (GNews)
  → Set (标准化为 { articles, source: "gnews" })

→ Merge (合并两条数据流)
  → AI Agent (统一摘要)
  → Telegram (发送)
```

### 批量 AI 处理

```
Google Sheets (读取 100 行数据)
  → SplitInBatches (每批 5 条)
    → AI Agent (逐批 GPT 处理)
  → Google Sheets (写回结果)
```

### 数据分流处理

```
Webhook (接收混合数据)
  → Switch (根据 type 字段分支)
    ├─ type="image"  → Image Processing Pipeline
    ├─ type="text"   → Text AI Pipeline
    └─ type="data"   → Data Storage Pipeline
```

## 参考工作流

| 文件 | 合并/分流模式 |
|------|-------------|
| `workflows/Http/0970_HTTP_Schedule_Create_Webhook.json` | 双 HTTP → Set → Merge |
| `workflows/Splitout/0958_Splitout_Webhook_Automation_Webhook.json` | 复杂 SplitOut 编排 |
| `workflows/Splitout/1934_Splitout_Schedule_Create_Scheduled.json` | SplitOut + 批量处理 |
| `workflows/Limit/1645_Limit_Splitout_Automation_Webhook.json` | Limit + SplitOut 联合 |

## 常见问题与经验

1. **Merge 模式选择**：Append（追加）、Combine（合并单个字段）、Merge by Index（按索引匹配）、Merge by Key（按键匹配）——根据需求选择正确的模式
2. **SplitOut vs SplitInBatches**：数据量 < 100 条用 `splitOut`（全量处理）；数据量 > 100 条用 `splitInBatches`（分批处理，避免超时和 API 限流）
3. **内存问题**：SplitOut 会把所有 items 展开在内存中，超大数组（>10000）谨慎使用
4. **Aggregate 妙用**：处理完多条数据后，用 Aggregate 将结果汇总为单条摘要
5. **数据丢失**：Merge 操作后，原始数据的某些字段可能丢失，用 Set 在 Merge 前保留需要的字段

## 升级路径

- 分流后需要条件判断 → 学习 **[L2-06 条件分支与过滤]()**
- 批量调用不同 AI 模型 → 学习 **[L3-06 多模型协作与路由]()**
