# AI 视频自动生成管道 - 使用文档

## 📋 系统概述

本系统是一套基于 **n8n + DeepSeek + RunningHub** 的 AI 视频自动生成管道，由 **1 个主工作流 + 5 个子工作流** 组成，实现从创意到成片的端到端自动化。

**核心能力**：输入故事创意 → AI 自动创作角色形象、分镜脚本、配音文案 → 调用 RunningHub API 生成图像/视频/音频 → 自动合成带字幕和背景音乐的完整视频。

---

## 🏗️ 工作流清单

| 序号 | 文件名 | 工作流 ID | 类型 | 触发方式 |
|------|--------|-----------|------|---------|
| 1 | `主工作流_docker_.json` | `9bQRPbknpBALKk0l` | 主控 | 手动触发 |
| 2 | `视频工作流-生成人物.json` | `4rh85fateoFxhDYt` | 子工作流 | 被主工作流调用 |
| 3 | `视频工作流-生成分镜图片.json` | `NrSb0OIY3JcOH7yO` | 子工作流 | 被主工作流调用 |
| 4 | `视频工作流-生成视频.json` | `BIgQ9RmvnljUwTMd` | 子工作流 | 被主工作流调用 |
| 5 | `视频工作流-生成音频.json` | `hwjfzLwBMnif5vET` | 子工作流 | 被主工作流调用 |
| 6 | `视频生成-生成背景音乐.json` | `95zRg5w3oIdNynPt` | 子工作流 | 被主工作流调用 |

---

## 🔗 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    主工作流 (总控编排)                              │
│                                                                 │
│  手动触发 → 配置 → AI创作(角色+分镜+配音+字幕) → 5次子工作流调用      │
│       → 视频拼接 → 字幕合成 → 背景音乐合成 → 最终视频                │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
   ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌──────────┐
   │生成人物│ │生成分镜│ │生成视频│ │生成音频│ │生成背景音乐│
   │RunningHub│ │RunningHub│ │RunningHub│ │RunningHub│ │RunningHub  │
   └───────┘ └───────┘ └───────┘ └───────┘ └──────────┘
```

---

## 📦 依赖服务

| 服务 | 用途 | 配置方式 |
|------|------|---------|
| **DeepSeek API** | AI 文本创作（角色、分镜、配音、字幕、音乐提示词） | n8n Credential `DeepSeek account` |
| **RunningHub API** | 图像生成、图生视频、语音克隆、背景音乐生成 | `基础字段配置` 中的 `runninghub_apikey` |
| **n8n 工作流调用** | 子工作流通过 `executeWorkflow` 节点被主工作流调用 | `基础字段配置` 中的各 `工作流id-*` |

---

## 🎬 主工作流详解

### 文件：`主工作流_docker_.json`

### 节点结构（42 个节点）

#### 配置区域

| 节点名 | 类型 | 配置项 | 说明 |
|--------|------|--------|------|
| `基础字段配置` | Set | `output_folder_path`、`runninghub_apikey`、5 个子工作流 ID | 全局配置，运行时修改 |
| `视频字段配置` | Set | `video_ratio`、`max_image_count`、`story`、`artistic_style` | 创作参数 |
| `创建子文件夹` | Execute Command | `mkdir -p <output_path>` | 创建输出目录 |
| `图片比例计算` | Code | 根据 `video_ratio` 计算图片宽高 | 支持 7 种比例 |
| `视频比例计算` | Code | 根据 `video_ratio` 计算视频宽高 | 与图片比例对应 |

#### AI 创作流程（4 个 DeepSeek Agent）

| 序号 | 节点名 | LLM 模型 | 输出 | 说明 |
|------|--------|----------|------|------|
| 1 | `生成角色形象描述` | deepseek-reasoner | `character_prompt` | 生成角色外观描述 |
| 2 | `生成视频分镜脚本` | deepseek-reasoner | `storyboard_prompts[]` | 每镜含 prompt/duration/description |
| 3 | `生成语音脚本` | deepseek-reasoner | `voice_scripts[]` + `characters_timbre[]` | 配音方案 |
| 4 | `生成字幕文件` | deepseek-reasoner | `subtitle_text` | SRT 格式字幕 |

> **注意**：节点 1→2 串行（分镜依赖角色），节点 3 依赖分镜数据。

#### 子工作流调用

| 调用节点 | 目标子工作流 | 输入 | 输出 |
|----------|-------------|------|------|
| `Call '视频工作流-生成人物'` | `视频工作流-生成人物` | prompt, width, height, runninghub_apikey, output_folder_path | character_url, character_filepath |
| `Call '视频工作流-生成分镜图片'` | `视频工作流-生成分镜图片` | character_filepath, prompt, runninghub_apikey, output_folder_path | images_filepath[], images_url[] |
| `Call '视频工作流-生成视频'` | `视频工作流-生成视频` | image_filepath, prompt, duration, width, height, runninghub_apikey, output_folder_path | video_filepath |
| `Call '视频工作流-生成音频'` | `视频工作流-生成音频` | voice_script, runninghub_apikey, output_folder_path, voice_example_folder_path | data[] (voice_filepath等) |
| `Call '视频生成-生成背景音乐'` | `视频生成-生成背景音乐` | storyboard_prompts, character, runninghub_apikey, output_folder_path | music_filepath |

#### 视频合成流程

| 序号 | 节点 | 输入 | 输出 |
|------|------|------|------|
| 1 | `Video Merge` | 所有视频片段路径 | `video_only_*.mp4` |
| 2 | `Video Composer` | 拼接视频 + 配音音频 + 字幕 | `video_dub_*.mp4` |
| 3 | `获取音频时长` | 背景音乐文件（FLAC） | `duration_ms` |
| 4 | `Video Composer3` | `video_dub_*.mp4` + 背景音乐 | **最终视频** `视频生成结果_*.mp4` |

#### 错误处理

| 策略 | 节点 |
|------|------|
| `retryOnFail: true, maxTries: 5` | 4 个 AI Agent 节点 |
| `retryOnFail: true, waitBetweenTries: 1000ms` | `生成角色形象描述`、`生成语音脚本` |
| RunningHub 任务失败重试 | 各子工作流内部 IF3→Wait1→重发任务 |

---

## 🟢 子工作流 1：视频工作流-生成人物

### 文件：`视频工作流-生成人物.json`

### 功能
根据角色描述（prompt）调用 RunningHub 生成角色形象图片。

### 流程
```
被调用 → 配置字段 → 发起 RunningHub 任务 → 轮询状态 → 下载图片 → 保存 → 返回字段
```

### 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `prompt` | string | 角色形象描述 |
| `width` | number | 图片宽度 |
| `height` | number | 图片高度 |
| `runninghub_apikey` | string | RunningHub API Key |
| `output_folder_path` | string | 输出目录 |

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `character_filepath` | string | 保存的角色图片路径 |
| `character_url` | string | RunningHub 图片 URL |

### RunningHub 配置
- **workflowId**: `1990684231770804225`
- **API 端点**:
  - 创建任务: `POST https://www.runninghub.cn/task/openapi/create`
  - 查询状态: `POST https://www.runninghub.cn/task/openapi/status`
  - 获取输出: `POST https://www.runninghub.cn/task/openapi/outputs`
- **重试策略**: 错误码 421/433/413 → 等待 10 秒 → 重新发起

### 输出文件命名
`character_{timestamp}_{random}.png`

---

## 🟢 子工作流 2：视频工作流-生成分镜图片

### 文件：`视频工作流-生成分镜图片.json`

### 功能
根据分镜图片 prompt 和角色参考图，调用 RunningHub 生成分镜首帧图片。

### 流程
```
被调用 → 配置字段 → 读取角色图 → 上传到 RunningHub → 发起任务 → 轮询 → 下载所有图片 → 聚合 → 返回
```

### 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `character_filepath` | string | 角色参考图路径 |
| `prompt` | string | 分镜图片 prompt（JSON 字符串） |
| `runninghub_apikey` | string | RunningHub API Key |
| `output_folder_path` | string | 输出目录 |

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `images_filepath` | array | 所有生成图片的文件路径 |
| `images_url` | array | 所有生成图片的 URL |

### RunningHub 配置
- **workflowId**: `1990008698095456257`
- **特殊处理**: 先上传角色参考图，再发起生成任务；输出结果过滤仅保留 PNG 文件
- **重试策略**: 错误码 421/433/413 → 等待 10 秒 → 重试

### 输出文件命名
`image_{timestamp}_{random}.png`（每张分镜图片）

---

## 🟢 子工作流 3：视频工作流-生成视频

### 文件：`视频工作流-生成视频.json`

### 功能
根据分镜首帧图片和视频 prompt，调用 RunningHub 执行图生视频。

### 流程
```
被调用 → 配置字段 → 读取图片 → 上传图片 → 发起任务 → 轮询 → 下载视频 → 保存 → 返回
```

### 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `image_filepath` | string | 首帧图片路径 |
| `prompt` | string | 视频 prompt（含动作描述） |
| `duration` | number | 视频时长（秒） |
| `width` | number | 视频宽度 |
| `height` | number | 视频高度 |
| `runninghub_apikey` | string | RunningHub API Key |
| `output_folder_path` | string | 输出目录 |

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `video_filepath` | string | 生成的视频文件路径 |

### RunningHub 配置
- **workflowId**: `1990685073034928130`
- **上传节点**: 上传图片到 `nodeId: 37`
- **配置节点**: width(nodeId:18), height(nodeId:16), duration(nodeId:17), prompt(nodeId:36)
- **重试策略**: 错误码 421/433/413 → 等待 10 秒 → 重试

### 输出文件命名
`video_fragment_{timestamp}_{random}.mp4`

---

## 🟢 子工作流 4：视频工作流-生成音频

### 文件：`视频工作流-生成音频.json`

### 功能
根据配音脚本和音色样本，通过 AI 音色匹配 + RunningHub 语音克隆生成配音音频。

### 流程
```
被调用 → 配置字段 → 生成音色列表(14种预置音色) → AI音色匹配 → 
分流处理音色样本 → 上传克隆音频 → 循环发起任务 → 下载音频 → 计算时长 → 聚合返回
```

### 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `voice_script` | object | 配音脚本（含 characters_timbre + voice_scripts） |
| `runninghub_apikey` | string | RunningHub API Key |
| `output_folder_path` | string | 输出目录 |
| `voice_example_folder_path` | string | 音色样本目录 |

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `data[]` | array | 每个元素包含: `voice_filepath`, `text`, `start_time`, `end_time`, `audio_length` |

### ⭐ 特色功能：AI 音色匹配

使用 DeepSeek 将配音脚本中的音色描述（如"温暖沉稳的男中音"）与 14 种预置音色自动匹配。

**14 种预置音色**（需放置在 `voice_example_folder_path` 目录下）：

| 文件名 | 描述 |
|--------|------|
| `活力女声.flac` | 有活力的青年女性声音 |
| `不羁男声.flac` | 潇洒不羁的青年男性声音 |
| `沉稳男声.flac` | 沉稳可靠的青年男性声音 |
| `成熟女声.flac` | 成熟稳重的中年女性声音 |
| `聪明儿童男声.flac` | 聪明的男孩声音 |
| `淡雅女声.flac` | 淡雅坚定的青年女性声音 |
| `搞笑大爷.flac` | 搞笑的中年男性声音 |
| `可爱儿童男声.flac` | 可爱的男孩声音 |
| `可爱儿童女声.flac` | 可爱的女孩声音 |
| `老年女声.flac` | 老年女性的声音 |
| `少年男声.flac` | 少年男性声音 |
| `甜美女声.flac` | 甜美的青年女性声音 |
| `温暖少女.flac` | 温暖的少年女性声音 |
| `温润男声.flac` | 温暖的青年男性声音 |

### RunningHub 配置
- **workflowId**: `1990236925644730369`
- **上传**: 克隆音频上传到 `nodeId: 9`
- **文本**: 配音文本配置到 `nodeId: 6`
- **重试策略**: 错误码 421/433/413 → 等待 10 秒 → 重试

### 输出文件命名
`audio_{timestamp}_{random}.flac`

---

## 🟡 子工作流 5：视频生成-生成背景音乐

### 文件：`视频生成-生成背景音乐.json`

### 功能
AI 分析角色和分镜内容，生成英文音乐 prompt，调用 RunningHub 生成背景音乐。

### 流程
```
被调用 → 配置字段 → Code计算总时长 → AI Agent生成音乐prompt → 发起任务 → 轮询 → 下载 → 保存 → 返回
```

### 输入参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `storyboard_prompts` | array | 分镜脚本数组 |
| `character` | string | 角色描述 |
| `runninghub_apikey` | string | RunningHub API Key |
| `output_folder_path` | string | 输出目录 |

### 输出

| 字段 | 类型 | 说明 |
|------|------|------|
| `music_filepath` | string | 背景音乐文件路径 |

### ⭐ 特色功能：AI 音乐配乐师

AI Agent 根据以下规则生成英文音乐 prompt：
1. **角色优先级原则**：音乐首先匹配角色年龄/气质，故事作为辅助
2. **极简主义**：只用 1 种乐器
3. **BPM 匹配**：儿童 85-115 BPM，成人 70-100 BPM
4. **乐器推荐表**：Xylophone(儿童)、Acoustic Guitar(少年)、Harp(女性)、Cello(严肃) 等

### RunningHub 配置
- **workflowId**: `1990596837553967106`
- **tags**: 音乐 prompt 配置到 `nodeId: 3`
- **seconds**: 时长配置到 `nodeId: 5`
- **重试策略**: 错误码 421/433/413 → 等待 10 秒 → 重试

### 输出文件命名
`music_{timestamp}_{random}.flac`

---

## ⚙️ 部署指南

### 1. 前置准备

```bash
# 目录结构要求
/data/
├── voice/                    # 音色样本目录（14个 .flac 文件）
│   ├── 活力女声.flac
│   ├── 不羁男声.flac
│   ├── 沉稳男声.flac
│   └── ... (共14个)
└── {timestamp}/             # 运行时的输出目录（自动创建）
    ├── character_*.png
    ├── image_*.png
    ├── video_fragment_*.mp4
    ├── audio_*.flac
    ├── music_*.flac
    ├── subtitle_*.srt
    ├── video_only_*.mp4
    ├── video_dub_*.mp4
    └── 视频生成结果_*.mp4   # 最终产物
```

### 2. 导入工作流

在 n8n 中按以下顺序导入：

1. 先导入 **5 个子工作流**（确保它们先获得工作流 ID）
2. 记录每个子工作流的 ID
3. 最后导入 **主工作流**

### 3. 配置凭证

| 凭证类型 | 节点 | 配置位置 |
|---------|------|---------|
| DeepSeek API Key | 5 个 DeepSeek Chat Model | n8n Credentials → DeepSeek |
| RunningHub API Key | `基础字段配置.runninghub_apikey` | 主工作流启动前填写 |

### 4. 配置主工作流

在 `基础字段配置` 节点中填写：

```javascript
{
  "output_folder_path": "=/data/",          // 输出根目录
  "runninghub_apikey": "your-runninghub-key", // RunningHub API Key
  "工作流id-生成人物": "4rh85fateoFxhDYt",     // 子工作流1的ID
  "工作流id-生成分镜图片": "NrSb0OIY3JcOH7yO",  // 子工作流2的ID
  "工作流id-生成视频": "BIgQ9RmvnljUwTMd",      // 子工作流3的ID
  "工作流id-生成音频": "hwjfzLwBMnif5vET",      // 子工作流4的ID
  "工作流id-生成背景音乐": "95zRg5w3oIdNynPt"    // 子工作流5的ID
}
```

在 `视频字段配置` 节点中配置创作参数：

```javascript
{
  "video_ratio": "3:4",                           // 视频比例
  "max_image_count": "2",                         // 最大分镜数
  "story": "一个小女孩在花园玩耍的故事",            // 故事核心
  "artistic_style": "3D皮克斯风格"                 // 艺术风格
}
```

> **支持的视频比例**: 1:1、4:3、3:4、3:2、2:3、16:9、9:16

### 5. 运行

1. 确保所有 6 个工作流已激活
2. 在 n8n 中打开主工作流
3. 点击 "Execute workflow" 触发

---

## 📊 执行时间估算

| 阶段 | 预估耗时 | 说明 |
|------|---------|------|
| AI 创作（角色+分镜+配音） | 30-60 秒 | 取决于 DeepSeek 响应速度 |
| 生成角色图片 | 30-120 秒 | RunningHub 队列+生成 |
| 生成分镜图片 | 每张 30-120 秒 | 并行或串行取决于配置 |
| 生成视频片段 | 每段 60-180 秒 | 图生视频耗时较长 |
| 生成配音音频 | 每段 30-60 秒 | 语音克隆 |
| 生成背景音乐 | 30-120 秒 | AI 音乐生成 |
| 视频合成 | 10-30 秒 | 本地处理 |
| **总计** | **5-15 分钟** | 以 2 个分镜估算 |

---

## ⚠️ 注意事项

### RunningHub API
- 所有子工作流都依赖 RunningHub 异步任务模式（发起→轮询→下载）
- 错误码 421/433/413 会自动重试
- 轮询间隔：任务排队/运行中 10-15 秒

### 文件路径
- 所有输出使用时间戳目录 `=/data/{yyyy-MM-dd_hh-mm-ss}/`
- `voice_example_folder_path` 计算方式：output_folder_path 上两级 + `/voice/`
- 确保 n8n 有文件系统读写权限

### AI 模型
- 统一使用 `deepseek-reasoner` 模型
- Agent 节点都配置了 `retryOnFail: true, maxTries: 5`
- 输出解析使用 Structured Output Parser 确保 JSON 格式

### 已禁用的节点
- 各子工作流的 `Edit Fields` / `When clicking 'Execute workflow'` 节点已禁用（调试用）
- 主工作流的 `Wait2` / `If2` / `Code in JavaScript3` 已禁用（人工确认功能）

---

## 🔧 故障排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 子工作流调用失败 | 工作流 ID 不正确 | 重新获取子工作流 ID 并更新 `基础字段配置` |
| RunningHub 任务一直排队 | API Key 无效或额度不足 | 检查 `runninghub_apikey` |
| 音色匹配失败 | 音色样本文件不存在 | 确认 `voice/` 目录下有 14 个 `.flac` 文件 |
| 视频合成失败 | 社区节点未安装 | 安装 `n8n-nodes-media-composition` 插件 |
| DeepSeek 返回非 JSON | AI 输出格式不稳定 | retryOnFail 会自动重试最多 5 次 |
| 输出目录权限不足 | Docker 挂载问题 | 确保 `/data/` 目录可写 |
