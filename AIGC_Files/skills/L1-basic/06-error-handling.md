---
name: l1-error-handling
level: L1
category: 可靠性与健壮性
requires: []
feeds_into: [l2-all, l3-all]
---

# L1-06 基础错误处理

## 概述

错误处理是每个生产级工作流的标配。AIGC_Files 集合中 59 个工作流显式集成了 `stopAndError` 节点，近 100% 的工作流启用了 `retryOnFail`。良好的错误处理让工作流在 API 异常、超时、数据格式错误等情况下优雅降级，而非静默失败。

## 适用场景

- 任何调用外部 API 的工作流（网络不可靠）
- 处理用户输入的工作流（格式不确定）
- 涉及付费 API 调用的工作流（避免无效消耗）
- 长时间运行的批处理任务

## 输入定义

### stopAndError 节点

| 参数 | 类型 | 说明 |
|------|------|------|
| `message` | `string` | 错误消息，会显示在执行日志中 |
| `errorType` | `string` | 错误类型标识 |

### 工作流 Settings（全局重试）

```json
{
  "settings": {
    "retryOnFail": true,
    "retryCount": 3,
    "retryDelay": 1000,
    "executionTimeout": 3600,
    "maxExecutions": 1000
  }
}
```

## 输出定义

错误处理不产生正常输出，但提供：
- 执行历史中的红色 ❌ 标记
- 错误消息可用于调试
- 如需通知，可搭配 Telegram/Slack 发送告警

## 节点组合模板

### 基础错误捕获模式

```
[任意节点]
  → 主输出: 正常流程
  → 错误输出: stopAndError (记录错误)
```

n8n 中每个节点都有隐式的错误输出端口。在 UI 中右键节点 → "Add Error Output" 即可连接。

### 推荐配置：三层防护

```
Layer 1 - 节点级: 每个关键节点挂 stopAndError
Layer 2 - 工作流级: retryOnFail + retryCount + retryDelay
Layer 3 - 监控级: Error Workflow (独立错误处理工作流)
```

### 错误 + 通知模式

```
HTTP Request
  ├─ 成功 → 正常流程
  └─ 失败 → stopAndError → Telegram/Slack (发送告警)
```

## 参考工作流

AIGC_Files 中几乎所有生产级工作流都使用了错误处理：

| 文件 | 错误处理方式 |
|------|-------------|
| `workflows/Telegram/Academic Assistant Chatbot (Telegram + OpenAI).json` | 单 stopAndError 节点 |
| `workflows/Code/1278_Code_Schedule_Monitor_Webhook.json` | 多层错误分支 |
| `workflows/Wait/1282_Wait_Code_Import_Webhook.json` | 复杂工作流中的分布式错误处理 |

## 常见问题与经验

1. **不要吞错误**：遇到错误不处理比静默失败更好——至少你能知道发生了什么
2. **retryOnFail 的代价**：对付费 API（如 OpenAI），重试会产生额外费用。对可预期的错误（如输入校验失败），不应重试
3. **Error Workflow 模式**：配置一个独立的错误处理工作流（Settings → Error Workflow），集中处理所有工作流的异常
4. **Sticky Note 文档化**：在复杂工作流中，用 Sticky Note 标注每个分支可能出现的异常和处理策略
5. **超时配置**：AI 模型调用可能耗时较长，适当增大 `executionTimeout`（默认 3600 秒）

## 升级路径

- 了解所有节点类型后 → 回顾本技能，确保每个工作流都有适当的错误处理
- 构建复杂编排 → 参考 **[L3-08 业务全流程编排]()** 中的错误传递模式
