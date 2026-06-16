---
name: l2-google-sheets
level: L2
category: 数据处理与API集成
requires: [l2-http-api, l2-data-transform]
feeds_into: [l2-condition-filter, l3-ai-text-gen, l3-business-orchestration]
---

# L2-04 Google Sheets 读写

## 概述

Google Sheets 是 n8n 中最常用的"轻量数据库"。在 AIGC_Files 集合中出现了 **285 次**，是排名第七的集成服务。它既可以作为触发源（Sheet 更新时启动工作流），也可以作为数据存储目标（AI 处理结果写回），还能充当人机协作的界面。

## 适用场景

- 用户提交的数据批量 AI 处理
- AI 生成内容的结果存储
- 作为简易 CRM/数据库的数据源
- 人机协作：Google Sheets 编辑 → n8n 自动处理
- 批量数据导入导出

## 输入定义

### 读取数据

| 参数 | 说明 |
|------|------|
| Document ID | Google Sheets 文档 ID |
| Sheet Name / Range | 工作表名称或范围（如 `Sheet1!A1:Z100`） |
| Data Start Row | 数据起始行（0-based） |

### 写入数据

| 参数 | 说明 |
|------|------|
| Operation | `append` / `update` / `upsert` |
| Columns | 列映射（JSON 字段 → Sheet 列） |

## 输出定义

读取时返回数组格式：

```
[
  { "Name": "...", "Email": "...", "Score": "..." },
  { "Name": "...", "Email": "...", "Score": "..." }
]
```

## 节点组合模板

### AI 评分工作流

```
Google Sheets Trigger (检测新行)
  → Set (提取需要 AI 处理的列)
  → AI Agent (GPT-4 评分/分类)
  → Google Sheets (写回结果列)
```

### 批量数据导入

```
HTTP Request (获取外部数据)
  → Set (映射为标准格式)
  → Google Sheets (append 到目标 Sheet)
```

### AI 增强数据流水线

```
Google Sheets (读取待处理数据)
  → SplitInBatches (分批处理)
    → AI Agent (逐条 AI 分析)
  → Google Sheets (批量写回)
```

### 数据清洗回写模式

```
Google Sheets (读取原始数据)
  → Code (清洗+补全+校验)
    过程: 日期标准化、缺失值补全、异常标记
  → Google Sheets (update 写回，按订单ID匹配)
```

> **关键**: 使用 `update` 操作 + `matchingColumns: ["订单ID"]` 精确写回对应行，而非追加。

## 参考工作流

| 文件 | Sheets 使用模式 |
|------|----------------|
| `workflows/Openai/1177_Openai_GoogleSheets_Create_Triggered.json` | Sheets + OpenAI 评分 |
| `workflows/Manual/1543_Manual_Openai_Automation_Triggered.json` | Sheets 反馈摘要 |
| `workflows/Webhook/1694_Webhook_HTTP_Automation_Webhook.json` | Sheets 数据丰富 |
| `workflows/Http/1811_HTTP_GoogleSheets_Automate_Webhook.json` | Sheets 数据提取 |
| **`Workflow/ xiaolin/ExcelAutoCleaning.json`** | **Google Sheets 读取→清洗→写回（完整管道）** |

## 常见问题与经验

1. **认证**：需要配置 Google Cloud OAuth2 凭据，首次使用需授权 Sheets API 访问
2. **列名约定**：JSON 的 key 名必须与 Sheet 列名完全一致（大小写敏感），用 Set 节点提前处理
3. **写回策略**：`update` 需要指定行号，`append` 追加到末尾，`upsert` 按键值匹配更新
4. **速率限制**：Google Sheets API 有频率限制（每 100 秒约 60 次写操作），大批量写入用 `splitInBatches` + `wait` 控制节奏
5. **大文件警告**：超过 1000 行的 Sheet 读取会较慢，考虑用 `limit` 节点限制单次处理量
6. **URL 安全**：Sheet 的 Document ID 来自 URL：`https://docs.google.com/spreadsheets/d/{DOCUMENT_ID}/`

## 升级路径

- 数据需要条件过滤 → 学习 **[L2-06 条件分支与过滤]()**
- 大批量数据处理 → 学习 **[L3-08 业务全流程编排]()**
- 替代方案：结构化数据存储 → 学习 **[L2-07 数据库操作]()**
