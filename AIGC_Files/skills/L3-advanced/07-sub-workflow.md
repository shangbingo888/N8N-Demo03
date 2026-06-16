---
name: l3-sub-workflow
level: L3
category: AI多模型协作
requires: [l2-all, l3-ai-agent]
feeds_into: [l3-business-orchestration]
---

# L3-07 子工作流模块化

## 概述

当一个工作流变得过于复杂（>30 节点），将其拆分为多个可复用的子工作流是工程化的必然选择。Execute Workflow 节点让子工作流像函数一样被调用——接收输入、处理逻辑、返回输出。在 AIGC_Files 中，executeworkflow 出现 189 次，是排名第 12 的集成节点。

## 适用场景

- 大型工作流拆分（每个子工作流 < 20 节点）
- 可复用逻辑封装（AI 分类器、数据清洗、通知发送）
- 多 Agent 系统（每个 Agent 是一个子工作流）
- 作为 AI Agent 的 Tool 使用
- 团队协作（不同人维护不同子工作流）

## Execute Workflow 两种模式

### 模式 1：主流程调用子流程

```
主工作流:
  Manual Trigger
    → Execute Workflow (调用"数据清洗"子工作流)
    → Execute Workflow (调用"AI分析"子工作流)
    → Execute Workflow (调用"通知发送"子工作流)
```

### 模式 2：子工作流作为 Agent Tool

```
主工作流:
  AI Agent
    Tools: 
      - Workflow Tool → "邮件Agent"子工作流
      - Workflow Tool → "日历Agent"子工作流
      - Workflow Tool → "数据查询Agent"子工作流
```

### 模式 3：异步生成管道（RunningHub 模式）

```
主工作流 (42 节点):
  字段配置 → AI 创作 (DeepSeek × 4: 角色/分镜/配音/字幕)
    → Execute Workflow ("生成人物", workflowId X)
    → Execute Workflow ("生成分镜图片", workflowId Y)
    → Execute Workflow ("生成视频片段", workflowId Z)
    → Execute Workflow ("生成配音音频", workflowId W)
    → Execute Workflow ("生成背景音乐", workflowId V)
    → Video Merge → Video Composer → 最终视频

每个子工作流独立实现:
  Execute Workflow Trigger → 配置 → HTTP (创建任务) → Wait(轮询) → HTTP(下载) → Return
```

**关键设计**：
- 子工作流内部包含完整的异步任务处理（提交→轮询→下载→错误重试）
- 错误码 421/433/413 自动重试，不传播到主工作流
- 每个子工作流可独立测试和调试
- 导入顺序：先导入 5 个子工作流获取 ID，再导入主工作流

## 节点组合模板

### 主-子工作流架构

**主工作流：业务流程编排**
```
Telegram Trigger (用户需求)
  → AI Agent (理解需求，分配任务)
    Tools:
      - Execute Workflow → "🤖Contact Agent" (联系人管理)
      - Execute Workflow → "🤖Email Agent" (邮件处理)
      - Execute Workflow → "🤖Calendar Agent" (日程管理)
  → Telegram (返回结果)
```

**子工作流：Contact Agent**
```
Execute Workflow Trigger
  → Airtable Tool (查询/更新联系人)
  → Set (格式化结果)
  → Return to Workflow
```

### 工具调用子工作流

```
子工作流 (作为 Tool 被 Agent 调用):
  Execute Workflow Trigger (接收 Agent 的参数)
    → HTTP Request (调用外部 API)
    → Set (提取结果)
    → if (调用成功?)
      ├─ Yes → Return (返回结构化数据)
      └─ No  → Return (返回错误信息)
```

## 参考工作流

| 文件 | 子工作流模式 |
|------|------------|
| `workflows/Executeworkflow/1793_Executeworkflow_Airtabletool_Automation_Triggered.json` | Contact Agent 子工作流 |
| `workflows/Gmailtool/1795_Gmailtool_Executeworkflow_Send_Triggered.json` | Email Agent 子工作流 |
| `workflows/Googlecalendartool/1792_Googlecalendartool_Executeworkflow_Automation_Triggered.json` | Calendar Agent 子工作流 |
| `workflows/Aggregate/0681_Aggregate_HTTP_Create_Webhook.json` | 子工作流编排 |
| **`Workflow/WorkflowDemo01/主工作流_docker_.json`** | **RunningHub 视频生成：5 子工作流管道（人物/分镜/视频/音频/音乐）** |

## 常见问题与经验

1. **Caller Policy**：子工作流的 Settings → Caller Policy 控制谁可以调用。设为 `workflowsFromSameOwner`（白名单）是最安全的
2. **数据传递**：主工作流通过 Execute Workflow 的 Input 字段传递数据，子工作流通过 Return 节点返回数据
3. **错误传播**：子工作流错误默认传播到主工作流，可在主工作流中为 Execute Workflow 节点添加 Error Output
4. **版本管理**：子工作流修改后可能影响所有调用方，建议使用版本标记或独立副本
5. **循环调用**：避免子工作流互相调用形成死循环
6. **命名规范**：AIGC_Files 中使用 emoji 前缀（如 🤖Contact Agent）让子工作流在列表中更醒目

## 升级路径

- 多 Agent 系统集成 → 学习 **[L3-08 业务全流程编排]()**
- AI Agent + 子工作流 Tool → 回顾 **[L3-03 AI Agent 工具调用]()**
