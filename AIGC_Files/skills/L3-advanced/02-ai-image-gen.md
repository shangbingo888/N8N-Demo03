---
name: l3-ai-image-gen
level: L3
category: AI多模型协作
requires: [l2-http-api, l2-file-processing]
feeds_into: [l3-business-orchestration]
---

# L3-02 AI 图像生成

## 概述

AI 图像生成让工作流从"文本输入文本输出"扩展到"多模态内容生产"。AIGC_Files 涵盖了 OpenAI DALL-E / GPT-Image-1、Midjourney API、Flux (Fal.ai)、Kling、ComfyUI 等主流图像生成服务。图像生成通常需要异步轮询或长时间等待，因此工作流中频繁使用 `wait` 节点。

## 适用场景

- 用户输入 Prompt 即时生成图片
- 批量产品图/素材生成
- AI 驱动的设计原型
- 图像风格转换（DALL-E 重绘）
- 社交媒体内容自动化配图
- 视频生成流水线中的关键帧生成

## 主流服务对比

| 服务 | 接入方式 | 延迟 | 质量 | 使用场景 |
|------|----------|------|------|----------|
| OpenAI GPT-Image-1 | HTTP Request | 5-15s | 高 | 通用图片生成、海报生成 |
| DALL-E 3 | HTTP Request | 10-30s | 高 | 写实/艺术风格 |
| Midjourney | HTTP Request (第三方 API) | 30-120s | 极高 | 高质量艺术创作 |
| Flux (Fal.ai) | HTTP Request | 5-20s | 高 | 写实人像/场景 |
| Kling | HTTP Request | 30-180s | 高 | AI 视频生成 |
| **RunningHub** | HTTP Request (异步) | 30-180s | 高 | AI 视频生成管道全流程（角色/分镜/视频/音频/音乐） |
| ComfyUI | 自托管 API | 取决于 GPU | 可定制 | 高度自定义管线、本地 GPU 部署 |

## 节点组合模板

### 即时图像生成（OpenAI）

```
Form Trigger (Prompt + Size)
  → HTTP Request (POST /v1/images/generations)
    body: { model: "gpt-image-1", prompt, n: 1, size }
  → Convert to File (data[0].b64_json → Binary)
  → Form (返回图片下载)
```

### 异步图像生成（Midjourney / Kling）

```
Manual Trigger
  → HTTP Request (POST Midjourney API - 提交任务)
  → Wait (等待 60-120 秒轮询)
  → HTTP Request (GET 查询任务状态)
  → if (任务完成?)
    ├─ Yes → Convert to File → Google Drive (保存)
    └─ No  → Wait → 回到查询 (循环)
```

### AI 图片 + 文字融合内容生成

```
AI Agent (GPT-4o 生成创意文案和图片 Prompt)
  ├─ Branch 1: 文案处理 → 格式化
  └─ Branch 2: HTTP Request (图片生成) → Convert to File
  → Merge (图文合并)
  → Social Media Post (发布到 Instagram/Facebook/TikTok)
```

### RunningHub 视频生成管道

RunningHub 是一个完整的 AI 视频生成平台，通过异步 API 提供 5 类生成服务：

```
AI 创作层（DeepSeek Agent）:
  ├─ 生成角色形象描述 → character_prompt
  ├─ 生成视频分镜脚本 → storyboard_prompts[]
  ├─ 生成语音脚本 → voice_scripts[] + characters_timbre[]
  └─ 生成字幕文件 → subtitle_text (SRT)

RunningHub 执行层（5 个子工作流并行/串行调用）:
  ├─ 生成人物 (workflowId: 1990684231770804225) → character_url + character_filepath
  ├─ 生成分镜 (workflowId: 1990008698095456257) → images_filepath[] + images_url[]
  ├─ 生成视频 (workflowId: 1990685073034928130) → video_filepath
  ├─ 生成音频 (workflowId: 1990236925644730369) → voice_filepath[] （含 14 种音色匹配）
  └─ 背景音乐 (workflowId: 1990596837553967106) → music_filepath

合成层（n8n-nodes-media-composition）:
  → Video Merge (拼接视频片段) → Video Composer (字幕+配音) → Video Composer (背景音乐) → 最终视频
```

### 海报生成器（Form + AI 风格选择）

```
Form Trigger
  ├─ 主标题 (text, required)
  ├─ 副标题 (text, required)
  ├─ 辅助信息 (text)
  └─ 海报风格 (dropdown: 手写/3D/极简/赛博朋克/复古/霓虹/扁平/涂鸦/书法/像素/自然 共11种)

  → Code (拼接风格关键词到 Prompt)
  → OpenAI (gpt-image-1, quality: high, size: 1024x1536)
  → Form Completion (返回海报图片)
```

## 参考工作流

| 文件 | 图像生成模式 | 服务 |
|------|------------|------|
| `workflows/Form/1316_Form_Stickynote_Automation_Webhook.json` | 表单→图像→返回 | OpenAI |
| `workflows/Http/0688_HTTP_Webhook_Process_Webhook.json` | Lego 风格转换 | DALL-E |
| `workflows/Http/1152_HTTP_Stickynote_Automation_Webhook.json` | 图像生成模板 | OpenAI |
| `workflows/Wait/1456_Wait_HTTP_Automation_Webhook.json` | Flux 图像生成 | Fal.ai |
| `workflows/Wait/1484_Wait_Code_Create_Webhook.json` | Midjourney + Kling 动画 | Midjourney + Kling |
| `workflows/Manual/1238_Manual_Code_Automation_Webhook.json` | 3D Figurine 正交图 | Midjourney + GPT-4o |
| **`Workflow/WorkflowDemo01/`** | **RunningHub 视频生成管道（5 子工作流）** | **RunningHub** |
| **`Workflow/comfyui-workflow/`** | **ComfyUI 视频生成（自托管替代方案）** | **ComfyUI** |
| **`Workflow/ xiaolin/n8nposter.json`** | **海报生成器（11 种风格）** | **OpenAI** |

## 常见问题与经验

1. **异步处理模式**：Midjourney/Kling 需要提交任务→等待→轮询结果的异步模式，必须用 `wait` 节点控制
2. **Base64 编码**：OpenAI 返回的图片是 Base64 字符串，需要用 `convertToFile` 转为二进制
3. **API 费用**：图像生成 API 费用远高于文本生成（单张图 $0.02-0.12），添加确认步骤或限制防止意外消耗
4. **提示词工程**：图像生成的 Prompt 需要更精确的描述（风格、构图、色彩、光照），建议先让 GPT-4o 润色用户 Prompt
5. **图片大小**：生成的图片通常 1-5MB，通过 n8n Webhook 返回大图片可能超时，用 Form Completion 或存到 Google Drive 后发送链接
6. **ComfyUI 自托管**：通过 `httpRequest` 调用本地 ComfyUI API，需要 GPU 服务器和网络可达

## 升级路径

- 图文混合内容发布 → 学习 **[L3-08 业务全流程编排]()**
- 视频生成 → 结合 AI 文本 + 图像 + Kling 等视频 API
