# [Webhook] 00-文生视频（合并版）使用说明

> **工作流 ID**：`S5r7jE8tY3UJa15j` | **节点数**：18 | **状态**：active
> **最后更新**：2026-06-22 | **时区**：Asia/Shanghai
> **触发方式**：`POST http://localhost:7890/webhook/text-to-video`

---

## 一、整体架构

```
用户 POST 请求
  │ { prompt, duration }
  ▼
┌──────────────────────────────────────────────────────────┐
│ 1. 接收请求 (Webhook)                                     │
│ 2. 校验输入参数 (Code)          ← 快速失败：400          │
│ 3. 构建AI分镜Prompt (Code)      ← AI 自主决策风格/分镜数 │
│ 4. 调用AI生成分镜 (HTTP)        ← Agnes AI              │
│ 5. 解析分镜输出 (Code)           ← Stream 修复            │
│    ├─ [并行] ──────────────────────────────────┐         │
│    │                                           │         │
│    ▼ 图片支线                                  ▼ 音频支线│
│ 6a. 构建生图请求 (Code)         11b. 构建TTS请求 (Code)    │
│ 7a. 调用Agnes生图API (HTTP)     12b. 调用Mimo TTS (HTTP)  │
│ 8a. 提取图片URL (Code)          13b. Base64解码音频 (Code) │
│ 9a. 下载图片文件 (HTTP)         14b. 标准化音频输出 (Code) │
│ 10a. 标准化图片输出 (Code)                               │
│    └───┬──────────────────────────────┬───┘              │
│        ▼                              ▼                  │
│      15. 汇总结果 (Code)  ← 等待两支线都完成              │
│      16. 调用合成服务 (HTTP) ← composer:8899 (FFmpeg)     │
│      17. 检查视频结果 (Code) ← Stream 修复                │
│      18. 返回结果 (Respond)  ← JSON 响应                  │
└──────────────────────────────────────────────────────────┘
```

**核心设计理念**：用户只提供 `prompt`（意图描述）和 `duration`（目标时长），AI 全权负责内容分镜、视觉风格、叙事节奏的创意决策。

---

## 二、节点详细说明

### 1. 接收请求

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.webhook` v2.1 |
| **ID / 名称** | `webhook` / 接收请求 |
| **触发方式** | POST |

#### 输入参数

| 参数名 | 类型 | 必填 | 说明 | 来源 |
|--------|------|------|------|------|
| `body.prompt` | `string` | ✅ | 视频内容描述，AI 据此生成分镜脚本 | 用户 HTTP POST body |
| `body.duration` | `number (integer)` | ✅ | 视频目标时长（秒），范围 5-1800 | 用户 HTTP POST body |

**请求示例**：
```bash
curl -X POST http://localhost:7890/webhook/text-to-video \
  -H "Content-Type: application/json" \
  -d '{"prompt": "人工智能如何改变医疗行业", "duration": 60}'
```

#### 输出结果

| 字段 | 类型 | 去向 |
|------|------|------|
| `body.prompt` | `string` | → 校验输入参数 |
| `body.duration` | `number` | → 校验输入参数 |

原始 webhook body 完整透传。

---

### 2. 校验输入参数

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript, runOnceForAllItems) |
| **ID / 名称** | `validate-input` / 校验输入参数 |

#### 输入参数（来自 接收请求）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `body.prompt` | `string` | 上游 `$input.first().json.body.prompt` |
| `body.duration` | `number` | 上游 `$input.first().json.body.duration` |

#### 校验规则

| 字段 | 校验逻辑 |
|------|----------|
| `prompt` | 必填，类型为 string，trim 后不能为空 |
| `duration` | 必填，类型为整数，范围 5 ≤ duration ≤ 1800(30 分钟) |

#### 输出结果

**校验失败（立即返回，终止流水线）**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` = `false` | → 返回结果 (Respond) |
| `statusCode` | `number` = `400` | → 返回结果 |
| `errors` | `string[]` | → 返回结果 |

**校验通过**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `body.prompt` | `string` | → 构建AI分镜Prompt |
| `body.duration` | `number` | → 构建AI分镜Prompt |

原始数据完整透传。

---

### 3. 构建AI分镜Prompt

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript, runOnceForAllItems) |
| **ID / 名称** | `build-prompt` / 构建AI分镜Prompt |

#### 输入参数（来自 校验输入参数）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `body.prompt` | `string` | `$input.first().json.body.prompt` |
| `body.duration` | `number` | `$input.first().json.body.duration` |

#### 处理逻辑

1. 构建 system prompt：定义 AI 为"专业视频分镜师"，要求 AI 根据内容长度自动判断策略
   - 短文本（< 200 字）→ 自动补充风格和叙事结构
   - 长文本（≥ 200 字）→ 提取核心主题和关键信息点
   - 自动决定分镜数量（3-60 个）
   - 自动判断视觉风格
2. 构建 user prompt：拼接用户输入、时长目标、JSON 输出格式规范
3. 组装 OpenAI 兼容 API 请求体

#### 输出结果

| 字段 | 类型 | 去向 |
|------|------|------|
| `body` | `object` | → 调用AI生成分镜 |
| `body.model` | `string` = `"agnes-2.0-flash"` | AI 模型名 |
| `body.messages` | `array` | system + user 消息 |
| `body.response_format` | `object` = `{type: "json_object"}` | 强制 JSON 输出 |
| `body.temperature` | `number` = `0.7` | 创意度 |
| `originalInput` | `object` | 原始输入的引用备份 |

---

### 4. 调用AI生成分镜

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.httpRequest` v4.4 |
| **ID / 名称** | `call-ai` / 调用AI生成分镜 |

#### 输入参数（来自 构建AI分镜Prompt）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `body` (请求体) | `object` | `$json.body`（上一节点输出） |

#### 请求配置

| 配置项 | 值 |
|--------|-----|
| **方法** | `POST` |
| **URL** | `{{ $env.OPENAI_BASE_URL \|\| 'https://apihub.agnes-ai.com/v1' }}/chat/completions` |
| **认证** | `Bearer {{ $env.OPENAI_API_KEY }}` |
| **Content-Type** | `application/json` |
| **超时** | 120000 ms |

#### 输出结果（⚠️ Task Runner 下可能是 Stream）

| 场景 | 输出格式 | 去向 |
|------|----------|------|
| autodetect 成功 | 解析后的 JSON 对象（含 `id`, `choices`） | → 解析分镜输出 |
| autodetect 失败 | Node.js Readable Stream 对象（含 `_readableState`, `_outBuffer`） | → 解析分镜输出（用 Stream 修复） |

---

### 5. 解析分镜输出

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript, runOnceForAllItems) |
| **ID / 名称** | `parse-scenes` / 解析分镜输出 |

#### 输入参数（来自 调用AI生成分镜）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `item.json` | `object` 或 `Stream` | `$input.first().json` |

#### Stream 修复策略（三重路径）

| 路径 | 条件 | 处理方式 |
|------|------|----------|
| **A** | `data` 已是包含 `id`/`choices` 的 JSON 对象 | 直接 `JSON.stringify(data)` |
| **B** | `data._readableState` 存在（Stream 模式） | `Buffer.from(data._outBuffer.data)` + `lastIndexOf('}')` 截断 |
| **C** | `data.responseBody` 是字符串 | 直接使用 |

#### 输出结果

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` = `true` | — |
| `scenes` | `array<object>` | → 构建生图请求 / 构建TTS请求 / 汇总结果 |
| `scenes[].index` | `number` | 分镜序号（从 1 开始） |
| `scenes[].description` | `string` | 中文场景描述 |
| `scenes[].prompt` | `string` | 英文图片生成提示词 |
| `scenes[].narration` | `string` | 中文配音文本 |
| `scenes[].duration` | `number` (≥5) | 该场景时长（秒） |
| `firstScene` | `object \| null` | 第一个分镜（用于单图场景） |
| `allNarration` | `string` | 全部配音文本拼接（句号分隔） |
| `totalScenes` | `number` | 总分镜数 |
| `totalDuration` | `number` | AI 计算的总时长（秒） |

> ⚠️ **fork 模式**：此节点的一个输出同时流向两个下游节点（**构建生图请求** 和 **构建TTS请求**），两张支线并行执行。

---

### 6a. 构建生图请求

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript) |
| **ID / 名称** | `build-image-req` / 构建生图请求 |

#### 输入参数（来自 解析分镜输出）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `firstScene.prompt` | `string` | `$input.first().json.firstScene.prompt` |

#### 输出结果

| 字段 | 类型 | 去向 |
|------|------|------|
| `model` | `string` = `"agnes-image-2.1-flash"` | → 调用Agnes生图API |
| `prompt` | `string` | 英文图片生成提示词 |
| `size` | `string` = `"1024x1024"` | 图片尺寸 |
| `n` | `number` = `1` | 生成数量 |

---

### 7a. 调用Agnes生图API

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.httpRequest` v4.4 |
| **ID / 名称** | `call-agnes-img` / 调用Agnes生图API |
| **错误处理** | `onError: continueRegularOutput`（失败不阻断流水线） |

#### 输入参数（来自 构建生图请求）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| 请求体 | `object` | `$json`（上一节点输出整个对象） |

#### 请求配置

| 配置项 | 值 |
|--------|-----|
| **方法** | `POST` |
| **URL** | `https://apihub.agnes-ai.com/v1/images/generations` |
| **认证** | `Bearer {{ $env.AGNES_API_KEY }}` |
| **超时** | 60000 ms |
| **响应格式** | `json` |

#### 输出结果

| 场景 | 输出 | 去向 |
|------|------|------|
| 成功 | Agnes 图片生成响应（含 `data[].url`） | → 提取图片URL |
| 失败 | 错误响应（节点继续，由下游判断） | → 提取图片URL |

---

### 8a. 提取图片URL

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript, runOnceForAllItems) |
| **ID / 名称** | `extract-img-url` / 提取图片URL |

#### 输入参数（来自 调用Agnes生图API）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `item.json` | `object` 或 `Stream` | `$input.first().json` |

#### Stream 修复策略

同节点 5 的三重路径（JSON 直接解析 → `_outBuffer` 截断 → `_readableState.buffer` 拼接）。

#### 输出结果

**成功**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `imageUrl` | `string` | → 下载图片文件 |

**失败**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` = `false` | → 下载图片文件（节点不会失败，但下载无 URL） |
| `error` | `string` | 错误信息 |
| `provider` | `string` = `"agnes"` | 供应商标识 |

---

### 9a. 下载图片文件

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.httpRequest` v4.4 |
| **ID / 名称** | `download-img` / 下载图片文件 |
| **错误处理** | `onError: continueRegularOutput` |

#### 输入参数（来自 提取图片URL）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| URL | `string` | `{{ $json.imageUrl }}` |

#### 请求配置

| 配置项 | 值 |
|--------|-----|
| **方法** | `GET`（默认） |
| **响应格式** | `file`（输出为 binary data） |
| **超时** | 30000 ms |

#### 输出结果

| 字段 | 类型 | 去向 |
|------|------|------|
| `binary.data` | `binary` | → 标准化图片输出 |
| `binary.data.fileName` | `string` | 文件名 |
| `binary.data.mimeType` | `string` | MIME 类型（image/png） |
| `binary.data.fileSize` | `number` | 文件大小（字节） |

---

### 10a. 标准化图片输出

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript, runOnceForAllItems) |
| **ID / 名称** | `img-standardize` / 标准化图片输出 |

#### 输入参数（来自 下载图片文件）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `binary.data` | `binary \| undefined` | `$input.first().binary.data` |

#### 输出结果

**成功**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` = `true` | → 汇总结果 |
| `provider` | `string` = `"agnes"` | → 汇总结果 |
| `model` | `string` = `"agnes-image-2.1-flash"` | → 汇总结果 |
| `fileName` | `string` | → 汇总结果 |
| `mimeType` | `string` | → 汇总结果 |
| `fileSize` | `number` | → 汇总结果 |
| `binary.data` | `binary` | 透传原始图片二进制（不进入汇总节点） |

**失败**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` = `false` | → 汇总结果 |
| `error` | `string` | → 汇总结果 |
| `provider` | `string` = `"agnes"` | → 汇总结果 |

---

### 6b. 构建TTS请求

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript) |
| **ID / 名称** | `build-tts-req` / 构建TTS请求 |

#### 输入参数（来自 解析分镜输出）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `allNarration` | `string` | `$input.first().json.allNarration`（全部配音文本拼接） |

#### 输出结果

| 字段 | 类型 | 去向 |
|------|------|------|
| `model` | `string` = `"mimo-v2.5-tts"` | → 调用Mimo TTS API |
| `messages` | `array` | user 配音风格指令 + assistant 配音文本 |
| `audio.format` | `string` = `"mp3"` | 音频格式 |
| `audio.voice` | `string` = `"冰糖"` | 语音角色 |
| `stream` | `boolean` = `false` | 非流式 |

---

### 7b. 调用Mimo TTS API

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.httpRequest` v4.4 |
| **ID / 名称** | `call-mimo-tts` / 调用Mimo TTS API |
| **错误处理** | `onError: continueRegularOutput` |

#### 输入参数（来自 构建TTS请求）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| 请求体 | `object` | `$json`（上一节点输出整个对象） |

#### 请求配置

| 配置项 | 值 |
|--------|-----|
| **方法** | `POST` |
| **URL** | `https://api.xiaomimimo.com/v1/chat/completions` |
| **认证** | `api-key: {{ $env.MIMO_API_KEY }}` |
| **超时** | 60000 ms |
| **响应格式** | `json` |

#### 输出结果

| 场景 | 输出 | 去向 |
|------|------|------|
| 成功 | Mimo TTS 响应（含 `choices[].message.audio.data` Base64） | → Base64解码音频 |
| 失败 | 错误响应（节点继续） | → Base64解码音频 |

---

### 8b. Base64解码音频

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript, runOnceForAllItems) |
| **ID / 名称** | `decode-tts` / Base64解码音频 |

#### 输入参数（来自 调用Mimo TTS API）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `item.json` | `object` 或 `Stream` | `$input.first().json` |

#### Stream 修复策略

同节点 5 的三重路径。

#### 输出结果

**成功**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `status` | `string` = `"success"` | → 标准化音频输出 |
| `format` | `string` | 音频格式（如 `mp3`） |
| `provider` | `string` = `"mimo"` | → 标准化音频输出 |
| `fileName` | `string` | `tts-{timestamp}.{format}` |
| `binary.audio` | `binary` | Base64 解码后的音频 Buffer |

**失败**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` = `false` | → 标准化音频输出 |
| `error` | `string` | 错误信息 |
| `provider` | `string` = `"mimo"` | → 标准化音频输出 |

---

### 9b. 标准化音频输出

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript, runOnceForAllItems) |
| **ID / 名称** | `tts-standardize` / 标准化音频输出 |

#### 输入参数（来自 Base64解码音频）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `binary.audio` | `binary \| undefined` | `$input.first().binary.audio` |
| `json.format` | `string` | `$input.first().json.format` |

#### 输出结果

**成功**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` = `true` | → 汇总结果 |
| `provider` | `string` = `"mimo"` | → 汇总结果 |
| `model` | `string` = `"mimo-v2.5-tts"` | → 汇总结果 |
| `format` | `string` | → 汇总结果 |
| `fileName` | `string` = `"tts-output.mp3"` | → 汇总结果 |
| `mimeType` | `string` = `"audio/mpeg"` | → 汇总结果 |

**失败**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` = `false` | → 汇总结果 |
| `error` | `string` | → 汇总结果 |
| `provider` | `string` = `"mimo"` | → 汇总结果 |

---

### 10. 汇总结果

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript, runOnceForAllItems) |
| **ID / 名称** | `merge` / 汇总结果 |

#### 输入参数

| 参数名 | 类型 | 来源 | 说明 |
|--------|------|------|------|
| `allItems` | `array` | `$input.all()` | 从图片和音频支线汇聚的全部 item |
| `sceneData` | `object` | `$('解析分镜输出').first().json` | 跨节点引用分镜数据 |
| `imgUrlData` | `object` | `$('提取图片URL').first()` | 跨节点引用图片 URL |
| `imageItem` | `object` | allItems 中 `provider === 'agnes'` 的项 | 筛选图片结果 |
| `ttsItem` | `object` | allItems 中 `provider === 'mimo'` 的项 | 筛选音频结果 |

#### 输出结果

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` | → 调用合成服务 |
| `pipeline` | `string` | 流水线标识 |
| `stages.storyboard` | `object` | 分镜阶段状态（status, totalScenes, scenes） |
| `stages.imageGen` | `object` | 生图阶段状态（status, fileName） |
| `stages.ttsGen` | `object` | 配音阶段状态（status, fileName） |
| `composerPayload` | `object` | → 调用合成服务（请求体） |
| `composerPayload.image_url` | `string` | 图片 URL |
| `composerPayload.narration` | `string` | 配音文本 |
| `composerPayload.voice` | `string` = `"冰糖"` | 语音角色 |
| `composerPayload.format` | `string` = `"mp3"` | 音频格式 |
| `composerPayload.output_name` | `string` | `video_{timestamp}.mp4` |
| `hasAllInputs` | `boolean` | 是否具备合成所需全部输入 |
| `outputName` | `string` | 输出文件名 |
| `completedAt` | `string` (ISO 8601) | 完成时间 |

---

### 11. 调用合成服务

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.httpRequest` v4.4 |
| **ID / 名称** | `run-ffmpeg` / 调用合成服务 |

#### 输入参数（来自 汇总结果）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| 请求体 | `object` | `$json.composerPayload` |

#### 请求配置

| 配置项 | 值 |
|--------|-----|
| **方法** | `POST` |
| **URL** | `http://composer:8899/compose-with-tts`（Docker 内网） |
| **Content-Type** | `application/json` |
| **认证** | 无（内网服务） |
| **超时** | 180000 ms |
| **响应格式** | `json` |

#### 输出结果

composer 返回的 JSON（含 `success`, `fileName`, `fileUrl`, `fileSize` 或 `error`），去向 → 检查视频结果。

---

### 12. 检查视频结果

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.code` v2 (JavaScript, runOnceForAllItems) |
| **ID / 名称** | `check-video` / 检查视频结果 |

#### 输入参数（来自 调用合成服务）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `item.json` | `object` 或 `Stream` | `$input.first().json` |

#### Stream 修复策略

同节点 5 的三重路径。

#### 输出结果

**成功**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` = `true` | → 返回结果 |
| `pipeline` | `string` | 流水线标识 |
| `video.status` | `string` = `"complete"` | 合成状态 |
| `video.fileName` | `string` | 视频文件名 |
| `video.fileUrl` | `string` | 视频访问 URL |
| `video.fileSize` | `number` | 文件大小（字节） |
| `completedAt` | `string` (ISO 8601) | 完成时间 |

**失败**：

| 字段 | 类型 | 去向 |
|------|------|------|
| `success` | `boolean` = `false` | → 返回结果 |
| `video.status` | `string` = `"failed"` | 失败状态 |
| `video.error` | `string` | 错误信息 |

---

### 13. 返回结果

| 属性 | 值 |
|------|-----|
| **类型** | `n8n-nodes-base.respondToWebhook` v1.5 |
| **ID / 名称** | `respond` / 返回结果 |

#### 输入参数（来自 检查视频结果）

| 参数名 | 类型 | 来源 |
|--------|------|------|
| `$json` | `object` | 上游节点完整 JSON 输出 |

#### 输出结果

| 配置项 | 值 |
|--------|-----|
| **响应格式** | `json` |
| **响应体** | `{{ JSON.stringify($json) }}` |

最终 HTTP 响应即为上游节点的完整 JSON。

---

## 三、数据流转总览

```
用户 POST { prompt, duration }
 │
 ▼
[接收请求] → body: { prompt, duration }
 │
 ▼
[校验输入参数] → 通过: 透传 body / 失败: { success: false, statusCode: 400, errors }
 │
 ▼
[构建AI分镜Prompt] → body: { model, messages, response_format, temperature }, originalInput
 │
 ▼
[调用AI生成分镜] → HTTP Response (JSON 或 Stream)
 │
 ▼
[解析分镜输出] → { success, scenes[], firstScene, allNarration, totalScenes, totalDuration }
 │
 ├──→ [构建生图请求] → { model, prompt, size, n }
 │      │
 │      ▼
 │    [调用Agnes生图API] → HTTP Response (JSON 或 Stream)
 │      │
 │      ▼
 │    [提取图片URL] → { imageUrl }  或  { success: false, error }
 │      │
 │      ▼
 │    [下载图片文件] → binary.data
 │      │
 │      ▼
 │    [标准化图片输出] → { success, provider, model, fileName, mimeType, fileSize }
 │
 └──→ [构建TTS请求] → { model, messages, audio: { format, voice }, stream }
        │
        ▼
      [调用Mimo TTS API] → HTTP Response (JSON 或 Stream)
        │
        ▼
      [Base64解码音频] → { status, format, provider, fileName } + binary.audio
        │
        ▼
      [标准化音频输出] → { success, provider, model, format, fileName, mimeType }
 
   两支线汇聚 ↓
[汇总结果] → { success, stages, composerPayload, hasAllInputs, outputName }
 │
 ▼
[调用合成服务] → composer HTTP Response (JSON 或 Stream)
 │
 ▼
[检查视频结果] → { success, video: { status, fileName, fileUrl, fileSize } }
 │
 ▼
[返回结果] → HTTP 200 JSON 响应
```

---

## 四、典型响应示例

### 成功

```json
{
  "success": true,
  "pipeline": "视频生成流水线(Docker)",
  "video": {
    "status": "complete",
    "fileName": "video_1719034567890.mp4",
    "fileUrl": "/files/video_1719034567890.mp4",
    "fileSize": 5242880
  },
  "completedAt": "2026-06-22T02:16:07.890Z"
}
```

### 校验失败

```json
{
  "success": false,
  "statusCode": 400,
  "errors": [
    "缺少必填参数: prompt（视频内容描述）",
    "缺少必填参数: duration（视频时长，5-1800 的整数秒）"
  ]
}
```

### 合成失败

```json
{
  "success": false,
  "pipeline": "视频生成流水线(Docker)",
  "video": {
    "status": "failed",
    "error": "FFmpeg合成失败: 音频文件损坏"
  },
  "completedAt": "2026-06-22T02:16:07.890Z"
}
```

---

## 五、环境依赖

| 依赖项 | 说明 |
|--------|------|
| `$env.OPENAI_BASE_URL` | AI 模型 API 地址（默认 `https://apihub.agnes-ai.com/v1`） |
| `$env.OPENAI_API_KEY` | AI 模型认证密钥 |
| `$env.AGNES_API_KEY` | Agnes Image API 认证密钥 |
| `$env.MIMO_API_KEY` | Mimo TTS API 认证密钥 |
| `composer:8899` | Docker 内网视频合成服务 |
| `n8n-files:/files` | 共享存储卷（视频输出目录） |

---

## 六、已知限制与注意事项

| 项目 | 说明 |
|------|------|
| **Stream 问题** | HTTP Request V4.4 在 Task Runner 下可能返回 Readable Stream 而非 JSON，4 个 Code 节点已内置 `_outBuffer` 截断修复 |
| **单图模式** | 当前仅使用 `firstScene`（第一个分镜）生成一张图片用于合成，非多场景轮播 |
| **并行支线** | 图片和音频支线并行执行，但「汇总结果」必须等待两者都完成 |
| **超时设置** | AI 生成 120s / 生图 60s / TTS 60s / 合成 180s，长视频可能超时 |
| **分镜上限** | AI 最多生成 60 个分镜，每个 ≥5 秒，理论支持最长 5 分钟视频 |

---

> 排障指南请参阅 [`docs/project-memory-and-troubleshooting.md`](./project-memory-and-troubleshooting.md) 第二部分。
