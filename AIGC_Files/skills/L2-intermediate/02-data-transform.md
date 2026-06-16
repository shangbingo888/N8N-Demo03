---
name: l2-data-transform
level: L2
category: 数据处理与API集成
requires: [l1-webhook-trigger, l2-http-api]
feeds_into: [l2-merge-split, l2-google-sheets, l3-all]
---

# L2-02 数据转换与映射

## 概述

数据在不同系统间流转时，格式几乎总是不匹配的。Set 节点（出现 259 次）和 Code 节点（出现 80 次）是 n8n 中最核心的数据塑形工具。Set 适合声明式的字段映射，Code 适合编程式的复杂转换逻辑。

## 适用场景

- API 返回的原始 JSON 需要重新组织字段结构
- 为下游 AI 节点构造特定格式的 Prompt
- 数据写入前清洗（去空值、类型转换、单位换算）
- 从嵌套 JSON 中提取扁平字段

## 节点选择决策

| 场景 | 推荐节点 | 原因 |
|------|----------|------|
| 简单字段重命名/映射 | `Set` | 声明式，无代码 |
| 提取嵌套字段 | `Set` | 用表达式 `={{ $json.data.items[0] }}` |
| 条件赋值/复杂计算 | `Code` | JavaScript 灵活性 |
| 数组转换/过滤 | `Code` | `Array.map/filter` 更自然 |
| 数据校验 | `Code` | 可抛异常触发错误分支 |

## 节点组合模板

### Set 节点：字段映射

```json
{
  "type": "n8n-nodes-base.set",
  "name": "GNews: Map to articles",
  "parameters": {
    "assignments": {
      "assignments": [
        {
          "name": "articles",
          "type": "string",
          "value": "={{ $json.articles }}"
        },
        {
          "name": "source",
          "type": "string",
          "value": "='GNews'"
        },
        {
          "name": "processedAt",
          "type": "string",
          "value": "={{ $now.toISO() }}"
        }
      ]
    }
  }
}
```

### Code 节点：自定义转换

```javascript
// 输入: items (标准 n8n 数据格式)
// 输出: 转换后的 items

const results = [];

for (const item of $input.all()) {
  const raw = item.json;
  
  // 提取和转换
  results.push({
    json: {
      title: raw.title?.trim() || 'Untitled',
      url: raw.link || raw.url,
      summary: raw.description?.substring(0, 200),
      publishedAt: new Date(raw.pubDate).toISOString(),
      category: raw.category?.toLowerCase() || 'general'
    }
  });
}

return results;
```

### 常用表达式参考

| 表达式 | 作用 |
|--------|------|
| `={{ $json.field }}` | 访问当前节点的 JSON 字段 |
| `={{ $('NodeName').item.json.field }}` | 访问指定节点的字段 |
| `={{ $now.toISO() }}` | 当前时间 ISO 格式 |
| `={{ $json.articles[0].title }}` | 数组第一个元素的 title |
| `={{ $json.text.substring(0, 100) }}` | 截取前 100 字符 |
| `={{ $json.items.map(i => i.name).join(', ') }}` | 数组字段拼接 |
| `={{ $if($json.score > 0.8, 'high', 'low') }}` | 条件表达式 |

## 进阶模式：Excel 数据自动清洗

从 Workflow/ xiaolin/ExcelAutoCleaning.json 中提取的高级数据清洗模式：

```
Google Sheets (读取原始数据)
  → Code (数据清洗与补全)
    ├─ 日期格式标准化（支持 8+ 种格式：8位数字/7位/6位/5位/斜杠/点/MM-DD-YYYY/DD/MM/YYYY/中文年月日/英文月份）
    ├─ 缺失值补全（数量×单价→总金额、总金额÷单价→数量、总金额÷数量→单价）
    └─ 异常标记（记录所有补全/修正操作到"数据异常"字段）
  → Google Sheets (写回清洗后的数据)
```

**日期格式标准化函数**覆盖：
| 输入格式 | 示例 | 输出 |
|---------|------|------|
| 8位数字 | `20240501` | `2024-05-01` |
| 7位数字 | `2025529` | `2025-05-29` |
| 斜杠分割 | `2025/05/29` | `2025-05-29` |
| 点分割 | `2025.5.29` | `2025-05-29` |
| 中文格式 | `2025年5月29日` | `2025-05-29` |
| 英文月份 | `May 29, 2025` | `2025-05-29` |

## 参考工作流

| 文件 | 转换模式 |
|------|----------|
| `workflows/Http/0970_HTTP_Schedule_Create_Webhook.json` | Set 标准化双源数据 |
| `workflows/Code/1278_Code_Schedule_Monitor_Webhook.json` | Code 节点复杂数据清洗 |
| `workflows/Manual/1235_Manual_HTTP_Automation_Webhook.json` | 数据提取映射 |
| `workflows/Webhook/1694_Webhook_HTTP_Automation_Webhook.json` | 公司数据丰富与转换 |
| **`Workflow/ xiaolin/ExcelAutoCleaning.json`** | **Excel 数据自动清洗（日期标准化 + 缺失值补全 + 异常标记）** |

## 常见问题与经验

1. **Set vs Code**：能用 Set 不用 Code。Set 的表达式已覆盖 80% 的转换场景，且执行效率更高
2. **数据类型**：Set 节点的 `type` 参数决定输出类型（string/number/boolean/object/array），匹配下游节点的期望类型
3. **Code 节点模式**：首次返回 `$input.all()` 逐项处理；对于聚合操作使用 `$input.first()`
4. **调试**：在 Executions 面板可逐节点查看数据变化，这是 n8n 最强大的调试能力
5. **引用其他节点**：`$('NodeName')` 表达式确保节点名称不含特殊字符和空格

## 升级路径

- 多数据源需要合并 → 学习 **[L2-03 数据合并与分流]()**
- 写回 Google Sheets → 学习 **[L2-04 Google Sheets 读写]()**
- 为 AI 构造 Prompt → 学习 **[L3-01 AI 文本生成]()**
