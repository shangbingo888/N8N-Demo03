---
name: l1-manual-trigger
level: L1
category: 触发与响应
requires: []
feeds_into: [l2-all, l3-all]
---

# L1-05 手动触发与测试

## 概述

Manual Trigger 是 n8n 中的"万能开关"——点击即执行。它是开发和调试工作流的首选入口，也是手动触发批处理任务的标准方式。在 AIGC_Files 集合中，`manualTrigger` 出现了 96 次，是所有触发器中数量最多的。

## 适用场景

- **开发调试**：逐节点测试工作流逻辑，验证数据流转
- **手动批处理**：一次性任务（如批量数据导入、历史数据回填）
- **按需执行**：不需要自动触发、人工按需启动的任务
- **模板展示**：所有工作流模板的默认触发器

## 输入定义

Manual Trigger 无需外部数据输入。可以通过以下方式提供测试数据：

1. **Pin Data**：固定测试数据供后续节点使用
2. **Workflow Data**：从上一个执行的 workflow data 中获取
3. **手动输入**：在 n8n UI 中手动输入 JSON 数据

## 输出定义

Manual Trigger 输出取决于 Pin Data 或手动输入的数据，默认为空对象 `{}`。

## 节点组合模板

### 调试模式工作流

```
Manual Trigger (Pin Data 模拟输入)
  → HTTP Request (测试 API 调用)
  → Set (数据转换)
  → Code (自定义逻辑)
  → Stop and Error (观察异常分支)
```

### 手动批处理

```
Manual Trigger
  → Google Sheets (读取待处理数据)
  → SplitOut (逐行处理)
  → AI Agent (批量 AI 处理)
  → Google Sheets (写回结果)
```

## 参考工作流

| 文件 | 说明 |
|------|------|
| `workflows/Manual/1105_Manual_Stickynote_Automation_Webhook.json` | Text-to-Speech 测试 |
| `workflows/Manual/1303_Manual_Stickynote_Create_Triggered.json` | OpenAI Assistant 构建 |
| `workflows/Manual/1543_Manual_Openai_Automation_Triggered.json` | GPT-4 摘要反馈 |
| `workflows/Manual/1339_Manual_HTTP_Automation_Webhook.json` | OpenAI Fine-tuning |

## 常见问题与经验

1. **Pin Data 技巧**：右键节点 → Pin Data → 粘贴测试 JSON，即可在不运行前置节点的情况下测试后续逻辑
2. **执行日志**：每次手动执行都可在 Executions 面板查看详细日志、节点输入输出
3. **并发限制**：n8n 默认限制手动执行的最大并发数，大批量任务考虑用 Schedule Trigger
4. **生产切换**：开发完成将工作流转为 Active 后，将 Manual Trigger 替换为对应的业务触发器（Webhook/Schedule/Telegram）

## 升级路径

- 测试通过后转为自动化 → 学习 **[L1-01 Webhook 触发]()** / **[L1-02 定时任务]()** / **[L1-04 Telegram Bot]()**
- 需要批量数据处理 → 学习 **[L2-03 数据合并与分流]()**
- 集成 AI 处理 → 学习任意 L3 技能
