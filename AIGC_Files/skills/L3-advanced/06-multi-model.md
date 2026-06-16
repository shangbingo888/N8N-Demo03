---
name: l3-multi-model
level: L3
category: AI多模型协作
requires: [l3-ai-text-gen, l2-condition-filter, l2-merge-split]
feeds_into: [l3-business-orchestration]
---

# L3-06 多模型协作与路由

## 概述

单个 AI 模型无法胜任所有任务。多模型协作模式让你根据任务类型、成本、延迟、质量等维度动态选择最佳模型。AIGC_Files 中广泛使用了 OpenAI GPT-4o + Gemini + DeepSeek + Ollama 的组合策略，以及 LLM 路由器和模型比较器。

## 适用场景

- 根据任务复杂度路由到不同模型（简单→mini, 复杂→full）
- A/B 测试不同模型的输出质量
- 多模型并行处理同一输入后综合结果
- 成本优化：用廉价模型做预处理，昂贵模型做最终输出
- 模型降级：主模型不可用时切换到备选模型

## 协作模式

### 模式 1：智能路由

```
用户输入
  → Switch (根据复杂度/类型路由)
    ├─ 简单任务 → GPT-4o-mini (低成本)
    ├─ 复杂推理 → GPT-4o (高质量)
    ├─ 中文任务 → DeepSeek V3 (中文优化)
    └─ 多模态   → Gemini Flash (图像理解)
```

### 模式 2：并行比较

```
用户输入
  ├─ OpenAI GPT-4o (生成答案 A)
  ├─ Google Gemini (生成答案 B)
  └─ DeepSeek V3 (生成答案 C)
  → Merge (合并三个答案)
  → GPT-4o (评估并选出最佳答案)
  → 返回最佳结果
```

### 模式 3：模型降级链

```
HTTP Request (调用 GPT-4o)
  → if (成功?) 
    ├─ Yes → 返回结果
    └─ No  → HTTP Request (降级到 GPT-4o-mini)
              → if (成功?)
                ├─ Yes → 返回结果
                └─ No  → Telegram (告警: 所有模型不可用)
```

### 模式 4：平台路由（Model Selector）

n8n LangChain 的 Model Selector 节点支持按条件路由到不同 LLM 模型：

```
Form Trigger (选择创作类型: Twitter / 朋友圈 / 小红书)
  → Model Selector (@n8n/n8n-nodes-langchain.modelSelector)
    ├─ Twitter → AI Agent (Twitter 风格文案，短小精悍)
    ├─ 朋友圈 → AI Agent (朋友圈风格文案，亲切口语化)
    └─ 小红书 → AI Agent (小红书风格文案，emoji + 标签)
  → 格式化为最终输出
```

**Model Selector 配置**：
- `numberInputs`: 路由分支数（如上 3 路）
- `rule[].conditions[].leftValue`: `={{ $json.平台类型 }}`（动态判断）
- `rule[].conditions[].rightValue`: 固定值如 `"Twitter"`
- `rule[].conditions[].operator`: `string.equals`

## 节点组合模板

### 动态 LLM 路由器

```
Webhook (用户 Prompt + model_preference)
  → Switch (按 model_preference 路由)
    ├─ "gpt-4o"        → OpenAI Chat Model (gpt-4o)
    ├─ "gemini"        → HTTP Request (Gemini API)
    ├─ "deepseek"      → HTTP Request (DeepSeek API)
    └─ "local"         → HTTP Request (Ollama API)
  → AI Agent (统一处理输出)
  → Respond to Webhook
```

### LLM 基准测试比较器

```
Manual Trigger
  → Set (定义测试 Prompt)
  → SplitOut (分发给各模型)
    ├─ GPT-4o-mini
    ├─ GPT-4o
    ├─ Gemini Flash
    └─ DeepSeek V3
  → Merge (合并结果)
  → Google Sheets (记录对比数据:
      模型名称 | 耗时 | Token消耗 | 输出质量评分)
```

## 参考工作流

| 文件 | 多模型模式 | 模型组合 |
|------|-----------|----------|
| `workflows/Noop/1838_Noop_Stickynote_Automation_Triggered.json` | 动态 LLM 切换 | 多模型路由器 |
| `workflows/Splitout/1790_Splitout_Summarize_Automation_Triggered.json` | LLM 比较 | OpenAI + Google Sheets |
| `workflows/Datetime/1755_Datetime_Code_Automation_Webhook.json` | 本地多模型测试 | LM Studio |
| `workflows/Stickynote/1557_Stickynote_Automation_Triggered.json` | 自托管 LLM 路由器 | Ollama 多模型 |
| `workflows/Limit/1645_Limit_Splitout_Automation_Webhook.json` | DeepSeek + OpenAI 协作 | 多模型流水线 |
| **`Workflow/ xiaolin/AIAgentTool工作流.json`** | **Model Selector 平台路由** | **DeepSeek 多风格（Twitter/朋友圈/小红书）** |

## 常见问题与经验

1. **路由策略**：简单任务（分类、摘要、翻译）→ mini 模型；复杂任务（推理、创作、多步规划）→ full 模型
2. **OpenRouter 模式**：使用 OpenRouter API 作为统一入口，一个 Endpoint 访问 200+ 模型
3. **成本追踪**：多模型架构中 API 费用可能失控，在 Google Sheets 中记录每次调用的模型、Token、费用
4. **回退顺序**：设计 3 层降级链（主模型 → 备选模型 → 本地模型 → 人工兜底）
5. **输出一致性**：不同模型输出格式可能不同，统一用 `outputParserStructured` 约束输出 Schema

## 升级路径

- 全流程业务编排 → 学习 **[L3-08 业务全流程编排]()**
- 子工作流封装模型 → 学习 **[L3-07 子工作流模块化]()**
