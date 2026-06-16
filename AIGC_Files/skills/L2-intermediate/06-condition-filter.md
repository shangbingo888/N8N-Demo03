---
name: l2-condition-filter
level: L2
category: 数据处理与API集成
requires: [l2-data-transform, l2-merge-split]
feeds_into: [l3-multi-model, l3-business-orchestration]
---

# L2-06 条件分支与过滤

## 概述

if、switch、filter 三种节点让工作流具备了"决策能力"。在 AIGC_Files 中，if 出现 91 次，switch 出现 30 次，filter 出现 9 次。它们让工作流能够根据数据的实际内容动态选择执行路径——这是从"简单自动化"迈向"智能编排"的关键一步。

## 适用场景

- 根据 AI 输出结果分类路由
- 按数据质量过滤（排除空值、低置信度结果）
- 按用户输入选择不同的处理模型
- 多分支业务逻辑（如不同产品走不同审批流程）
- 限流保护（超过阈值则跳转告警分支）

## 核心节点对比

| 节点 | 用途 | 分支数 | 条件复杂度 |
|------|------|--------|-----------|
| `if` | 二元判断 | 2（True/False） | 简单比较 |
| `switch` | 多路分支 | 无限 | 多条件匹配 |
| `filter` | 数据过滤 | 2（通过/丢弃） | 比较 + 组合 |

### 选择决策

```
是否需要多路分支（>2条路径）？
  ├─ 是 → 使用 switch
  └─ 否 → 使用 if 或 filter
           ├─ 需要保留丢弃的数据 → if
           └─ 只需通过的数据 → filter
```

## 节点组合模板

### 基于 AI 输出分类路由

```
AI Agent (分析用户意图)
  → Switch (根据 intent 字段路由)
    ├─ intent="生成图片" → Image Generation Pipeline
    ├─ intent="查询数据" → Google Sheets Pipeline
    ├─ intent="翻译"     → Translation Pipeline
    └─ 默认              → General Chat Pipeline
```

### 数据质量过滤管道

```
HTTP Request (获取原始数据)
  → filter (排除空标题)
  → filter (排除低评分: score < 0.5)
  → Set (数据清洗)
  → Google Sheets (写入合格数据)
```

### 条件表达式参考

```
// if 节点常用条件
{{ $json.score > 0.7 }}                    // 数值比较
{{ $json.status === "active" }}            // 字符串匹配
{{ $json.tags.includes("priority") }}      // 数组包含
{{ $json.name !== undefined }}             // 存在性检查
{{ $json.items?.length > 0 }}              // 安全访问
{{ $now.diff($json.createdAt, 'hours') < 24 }}  // 时间差
```

## 参考工作流

| 文件 | 分支/过滤模式 |
|------|-------------|
| `workflows/Filter/1791_Filter_Summarize_Create_Triggered.json` | URL 过滤 + AI 摘要 |
| `workflows/Filter/1414_Filter_Summarize_Automation_Triggered.json` | Notion 页面过滤 → 向量存储 |
| `workflows/Limit/1645_Limit_Splitout_Automation_Webhook.json` | Limit + 条件处理 |
| `workflows/Code/1278_Code_Schedule_Monitor_Webhook.json` | 多条件 AI 监控 |

## 常见问题与经验

1. **条件顺序**：switch 节点按从上到下的顺序匹配，将最具体的条件放在最前面
2. **默认分支**：switch 节点务必设置 Fallback Output，处理未匹配到任何条件的情况
3. **空值陷阱**：`filter` 节点中 `value is empty` 的判断行为需注意——`""`、`null`、`undefined` 都被视为 empty
4. **组合条件**：复杂条件（AND/OR 组合）用 `filter` 节点或 Code 节点实现
5. **性能考虑**：大量 switch 分支时，用 Code 节点替代可能更高效

## 升级路径

- 按模型类型动态路由 → 学习 **[L3-06 多模型协作与路由]()**
- 复杂业务编排 → 学习 **[L3-08 业务全流程编排]()**
