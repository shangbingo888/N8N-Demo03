---
name: l3-business-orchestration
level: L3
category: AI多模型协作
requires: [l1-all, l2-all, l3-01-to-l3-07]
feeds_into: []
---

# L3-08 业务全流程编排

## 概述

业务全流程编排是 AIGC 技能体系的终极形态——将 L1-L3 的所有技能有机组合，构建端到端的商业解决方案。这些工作流通常包含 30-67 个节点，涉及 5+ 个外部服务，覆盖从数据获取、AI 处理、内容生成、多渠道分发到结果存储的完整链路。

## 适用场景

- AI 驱动的内容工厂（选题→写作→配图→多平台发布）
- 智能招聘管道（简历筛选→AI面试→评分→通知）
- 社交媒体全自动化（趋势捕捉→内容创作→定时发布）
- AI 视频生成工厂（脚本→配音→画面→剪辑→发布）
- 企业数据智能管道（采集→清洗→AI分析→报表→告警）

## 编排设计原则

### 1. 管道分段

将完整流程拆分为 4-5 个逻辑段：

```
[数据获取段] → [AI处理段] → [内容生成段] → [分发段] → [存储段]
```

### 2. 错误隔离

每个段有独立的错误处理，一段失败不影响其他段：

```
Segment A (数据获取)
  ├─ Success → Segment B
  └─ Error → Error Workflow → 通知
```

### 3. 并行加速

无依赖的段之间并行执行：

```
AI 处理段:
  ├─ 并行 1: 文本生成 (GPT-4o)
  ├─ 并行 2: 图片生成 (Flux)
  └─ 并行 3: 数据清洗 (Code)
→ Merge (汇合)
```

## 节点组合模板

### AI 社交媒体视频工厂（51 节点示例）

```
阶段 1 - 选题与数据获取:
  Schedule Trigger (每天触发)
    → HTTP Request (获取热点趋势)
    → AI Agent (GPT-4o 选题决策)

阶段 2 - AI 内容创作 (并行):
  ┌─ Branch A: AI Agent (脚本撰写)
  │     → OpenAI TTS (配音生成)
  ├─ Branch B: AI Agent (图片 Prompt 生成)
  │     → HTTP Request (Flux/Kling 图片生成)
  └─ Branch C: AI Agent (音乐/字幕)
        → HTTP Request (音频处理)

阶段 3 - 合成与发布:
  → HTTP Request (Creatomate API - 视频合成)
  → Google Drive (保存视频)
  → 多渠道分发 (并行):
      ├─ Instagram (发布)
      ├─ Facebook (发布)
      ├─ TikTok (发布)
      └─ YouTube (发布)

阶段 4 - 结果追踪:
  → Google Sheets (记录发布日志)
  → Telegram (通知完成)
```

### AI 智能招聘管道（67 节点示例）

```
阶段 1 - 简历获取与解析:
  Form Trigger (上传简历)
    → Extract from File (PDF 文本提取)
    → Information Extractor (结构化解析)
    → Google Sheets (存储候选人信息)

阶段 2 - AI 评估:
  → AI Agent (GPT-4o - 简历评分)
    Criteria: 技能匹配度、经验相关性、教育背景
  → Switch (按评分分流):
      ├─ 高分 (≥80): 进入面试环节
      ├─ 中分 (60-79): 进入人工审核
      └─ 低分 (<60): 发送婉拒邮件

阶段 3 - AI 面试:
  → AI Agent (Gemini - 行为面试题生成)
  → Wait (推送面试链接)
  → HTTP Request (接收面试回答)
  → AI Agent (评估面试表现)

阶段 4 - 结果通知:
  → Notion (更新 ATS 系统)
  → Gmail (发送 offer / 婉拒)
  → Slack (通知 HR 团队)
  → Telegram (通知面试官)
```

### AI 音色匹配管道

在配音工作流中，将自然语言音色描述自动匹配到预置音色库：

```
输入: voice_script.characters_timbre[] (如 "温暖沉稳的男中音")
  → AI Agent (DeepSeek - 将音色描述匹配到预置库)
    Preset: 14 种音色 (活力女声/不羁男声/沉稳男声/成熟女声/聪明儿童男声/
            淡雅女声/搞笑大爷/可爱儿童男声/可爱儿童女声/老年女声/少年男声/甜美女声/温暖少女/温润男声)
  → SplitOut (逐条处理配音)
  → HTTP Request (RunningHub 语音克隆 API)
  → 下载 → 合并配音
```

### AI 音乐配乐师

AI 根据视频内容自动生成背景音乐 Prompt：

```
输入: character + storyboard_prompts[]
  → Code (计算视频总时长)
  → AI Agent (音乐配乐师规则)
    Prompt 规则:
    - 角色优先级：音乐先匹配角色年龄/气质，故事为辅助
    - 极简主义：只用 1 种乐器
    - BPM 匹配：儿童 85-115，成人 70-100
    - 乐器推荐：Xylophone(儿童)/Acoustic Guitar(少年)/Harp(女性)/Cello(严肃)/...
  → HTTP Request (RunningHub 音乐生成) → 下载背景音乐
```

## 参考工作流

| 文件 | 节点数 | 业务场景 |
|------|--------|----------|
| `workflows/Wait/1282_Wait_Code_Import_Webhook.json` | 51 | AI 短视频工厂 (OpenAI + Flux + Kling + ElevenLabs) |
| `workflows/Wait/1639_Wait_Webhook_Automation_Webhook.json` | 67 | 智能招聘 (Gemini + ElevenLabs + Notion) |
| `workflows/Telegram/1288_Telegram_Wait_Automation_Webhook.json` | 38 | 社交媒体视频生成 (GPT-4 + Kling + Blotato) |
| `workflows/Telegram/1470_Telegram_Code_Create_Webhook.json` | 44 | Instagram 内容生成 (AI 图像生成) |
| `workflows/Wait/1395_Wait_Code_Create_Webhook.json` | 51 | 动画故事生成 (GPT-4o + Midjourney + Kling) |
| **`Workflow/workflow.json`** | **25** | **播客生成管道 (DeepSeek + SerpAPI + MiniMax TTS + Audio Merge)** |
| **`Workflow/WorkflowDemo01/主工作流_docker_.json`** | **42** | **AI 视频生成管道 (DeepSeek × 4 + RunningHub × 5 + 视频合成)** |
| **`Workflow/ xiaolin/Web内容摘要与多平台文案.json`** | **~15** | **网页→摘要→Notion+Telegram 多平台分发** |

## 常见问题与经验

1. **复杂度管理**：超过 30 节点的单一工作流难以维护。及时用 Execute Workflow 拆分为子流程
2. **执行超时**：全流程编排工作流可能超过默认的 3600 秒超时限制，在 Settings 中适当增大或改用子工作流
3. **幂等性设计**：定时触发的全流程工作流必须考虑重复执行问题——通过唯一 ID 或状态字段防止重复处理
4. **外部服务依赖**：多服务编排中任一 API 不可用都可能导致流程中断。为核心节点配置 fallback 机制
5. **监控与告警**：大工作流出问题时难以定位。在关键节点添加 Telegram/Slack 告警，记录执行状态到 Google Sheets
6. **渐进式构建**：不要试图一次性构建 50 节点的工作流。先完成最小可行版本（MVP），逐步添加新阶段

## 渐进式构建方法论

### Step 1: MVP（5-10 节点）
只实现核心价值链路，如 "输入 Prompt → AI 生成 → 返回结果"

### Step 2: 增强（10-20 节点）
添加数据验证、错误处理、结果存储

### Step 3: 多模态（20-35 节点）
引入图片/视频/音频生成，多服务并行

### Step 4: 全流程（35-70 节点）
添加分发、追踪、监控、降级等生产级能力

> **黄金法则**：每个 Step 都可独立运行且产生价值。不要构建一个庞大但一次都没跑通的工作流。
