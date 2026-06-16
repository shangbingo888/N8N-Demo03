---
name: l2-http-api
level: L2
category: 数据处理与API集成
requires: [l1-webhook-trigger, l1-schedule-trigger]
feeds_into: [l2-data-transform, l3-ai-text-gen, l3-ai-image-gen, l3-business-orchestration]
---

# L2-01 HTTP API 调用与集成

## 概述

HTTP Request 节点是 n8n 连接外部世界的"万能钥匙"。在 AIGC_Files 集合中，它出现了 **822 次**（所有集成中排名第一）。通过它，工作流可以调用任何 REST API——从 OpenAI、Gemini、DeepSeek 等 AI 模型，到 Google Sheets API、GitHub API，再到任意第三方服务。

## 适用场景

- 调用 AI 模型 API（OpenAI Chat、DALL-E、Gemini、DeepSeek 等）
- 获取外部数据源（NewsAPI、RSS Feed、Bright Data 爬虫）
- 触发第三方 Webhook（Slack、Discord、企业微信）
- 跨系统数据同步（Airtable → Notion）

## 输入定义

| 参数 | 类型 | 说明 |
|------|------|------|
| `method` | `GET / POST / PUT / DELETE / PATCH` | HTTP 方法 |
| `url` | `string` | 请求 URL，支持 `$env`、`$json` 表达式 |
| `authentication` | `none / generic / predefined` | 认证方式 |
| `sendBody` | `boolean` | 是否发送请求体 |
| `bodyParameters` | `{name, value}[]` | POST/PUT 请求体参数 |
| `sendHeaders` | `boolean` | 是否自定义请求头 |
| `sendQuery` | `boolean` | 是否发送查询参数 |

## 输出定义

| 字段 | 说明 |
|------|------|
| `$json` | API 返回的 JSON 数据 |
| `$binary` | 二进制响应（图片、文件等） |
| `$response.headers` | 响应头信息 |
| `$response.statusCode` | HTTP 状态码 |

## 节点组合模板

### 调用 OpenAI API（图像生成）

```
HTTP Request
  method: POST
  url: "{{ $env.API_BASE_URL }}/v1/images/generations"
  authentication: Header Auth
  headers: { "Authorization": "Bearer {{ $credentials.apiKey }}" }
  body: {
    "model": "gpt-image-1",
    "prompt": "={{ $json.Prompt }}",
    "n": 1,
    "size": "={{ $json['Image size'] }}"
  }
```

### 多数据源并行获取

```
Schedule Trigger
  ├─ HTTP Request (NewsAPI - AI 新闻)
  │    url: "https://newsapi.org/v2/everything?q=AI"
  │    headers: { "X-Api-Key": "..." }
  │
  └─ HTTP Request (GNews - AI 新闻)
       url: "https://gnews.io/api/v4/search?q=AI"
       query: { "token": "..." }

  → Set (标准化字段) → Merge (合并数据) → AI Agent (统一处理)
```

### 请求认证模式

| 认证类型 | 配置方式 |
|----------|----------|
| **Bearer Token** | Header Auth: `Authorization: Bearer {{ $credentials.token }}` |
| **API Key Query** | Query Auth: `api_key` 参数 |
| **Basic Auth** | Generic Credential: username + password |
| **OAuth2** | 使用 n8n 内置 OAuth2 机制 |

## 参考工作流

| 文件 | API 调用模式 |
|------|------------|
| `workflows/Http/0970_HTTP_Schedule_Create_Webhook.json` | 双源并行 HTTP + Merge |
| `workflows/Http/0688_HTTP_Webhook_Process_Webhook.json` | DALL-E 图像生成 API |
| `workflows/Http/1519_HTTP_Stickynote_Automation_Webhook.json` | DeepSeek API 调用 |
| `workflows/Manual/0337_Manual_Stickynote_Automation_Webhook.json` | Bright Data 爬虫 API |
| `workflows/Form/1316_Form_Stickynote_Automation_Webhook.json` | OpenAI Image API + Form 返回 |

## 进阶模式：异步任务 API

### RunningHub 提交→轮询→下载模式

许多 AI 生成服务（RunningHub、Midjourney、Kling）采用异步任务模式：

```
HTTP Request (POST /create - 提交任务，获取 taskId)
  → Wait (等待 10-15 秒)
  → HTTP Request (POST /status - 查询任务状态)
  → IF (状态判断)
    ├─ 完成 → HTTP Request (POST /outputs - 下载结果)
    ├─ 排队/运行中 → 回到 Wait 循环
    └─ 失败 → IF 错误码判断
        ├─ 421/433/413 → Wait(10s) → 重新提交任务
        └─ 其他 → stopAndError
```

**错误码重试策略**：
| 错误码 | 含义 | 处理方式 |
|-------|------|----------|
| 421 | 队列繁忙 | 等待 10s 重试 |
| 433 | 生成超时 | 重新发起任务 |
| 413 | 资源不足 | 等待 10s 重试 |

### TTS 音频合成 API

| 服务 | API 端点 | 音频格式 | 解码方式 |
|------|---------|----------|----------|
| **Mimo TTS** | `https://api.xiaomimimo.com/v1/chat/completions` | Base64 WAV | `Buffer.from(base64, 'base64')` |
| **MiniMax TTS** | `https://api.minimaxi.com/v1/t2a_v2` | Hex MP3 | `Buffer.from(hexString, 'hex')` |
| **OpenAI TTS** | `https://api.openai.com/v1/audio/speech` | Binary MP3 | 直接二进制 |

**TTS 管道模式**：
```
HTTP Request (调用 TTS API)
  → Code (解码 Base64/Hex → Binary)
  → Write Binary File (保存音频文件)
  → Audio Merge (拼接多段音频，需要 n8n-nodes-media-composition 社区节点)
```

### 文件上传到外部 API

```
Read Binary Files (读取本地文件)
  → HTTP Request
      contentType: "binaryData"
      inputDataFieldName: "data"
```

## 常见问题与经验

1. **分页处理**：API 返回大量数据时，需要循环分页。组合 `splitInBatches` 或自定义 Code 节点处理 `next_page_token`
2. **速率限制**：公共 API 通常有 Rate Limit（如每分钟 60 次），用 `wait` 节点控制请求频率
3. **错误响应**：始终为 HTTP Request 节点添加 Error Output → stopAndError，处理 4xx/5xx 响应
4. **环境变量**：API URL、Key 等敏感信息用 `$env` 表达式引用，不要硬编码
5. **超时配置**：调用 AI 模型 API 时，HTTP Request 默认超时可能不够，调整为 60-120 秒
6. **数据提取**：API 返回嵌套 JSON 时，用表达式 `={{ $json.data.items[0].title }}` 提取深层字段
7. **异步轮询**：RunningHub/Midjourney/Kling 等异步 API，使用 IF + Wait 循环轮询状态，注意区分可重试错误（421/433/413）和不可重试错误
8. **音频解码**：不同 TTS 服务返回不同编码格式（Base64/Hex/Binary），需用对应的 `Buffer.from()` 方法解码

## 参考工作流（新增）

| 文件 | API 调用模式 |
|------|------------|
| `Workflow/current_state.json` | Webhook → DeepSeek → Mimo TTS → Base64 解码 → 写文件 |
| `Workflow/workflow.json` | DeepSeek Agent + SerpAPI 搜索 → MiniMax TTS → hex 解码 → Audio Merge |
| `Workflow/WorkflowDemo01/` | RunningHub 异步任务管道（提交→轮询→下载）× 5 个子工作流 |
| `Workflow/ xiaolin/Google RAG Workflow with MCP.json` | Google File Search Store API 文件上传 |
| `Workflow/ xiaolin/多平台数据监控(雷达)工作流.json` | 7 路并行 RSS Feed Read + RSSHub 代理 |

## 升级路径

- 返回数据需要结构化处理 → 学习 **[L2-02 数据转换与映射]()**
- 对接 AI 模型 → 学习 **[L3-01 AI 文本生成]()** / **[L3-02 AI 图像生成]()**
- 音频/视频生成管道 → 学习 **[L3-08 业务全流程编排]()**
