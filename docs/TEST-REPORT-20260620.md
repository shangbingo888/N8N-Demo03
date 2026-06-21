# 工作流测试报告

**日期**: 2026-06-20 09:18-09:28  
**测试环境**: n8n localhost:7890 (Docker: n8n-demo03)

---

## 测试结果汇总

| # | 工作流 | ID | 状态 | 耗时 | 结果 |
|---|--------|-----|------|------|------|
| 01 | 内容分析与分镜 | `JjMxOUIMgJBpwxer` | ✅ | 12.4s | 生成3个分镜脚本 |
| 02 | 文生图适配层 | `iD87BeQkqIZCLWiM` | ✅ | 32.3s | 生成并下载1.75MB PNG图片 |
| 03 | 文生音频适配层 | `7aA8FNq2ixjuphuX` | ✅ | 1.3s | 生成WAV音频文件 |
| 04 | 视频合成 | `MuNuZNCICl5kMqhQ` | ⚠️ 未测试 | - | 需提供图片和音频文件路径 |

---

## 详细结果

### 01-内容分析与分镜 ✅
- **输入**: 主题"一只在月球上漫步的猫咪", 科幻卡通风格, 3个分镜
- **输出**: 3个完整分镜（中文描述 + 英文生图Prompt + 中文配音文本）
- **AI模型**: agnes-2.0-flash
- **Token使用**: 943 tokens (479 prompt + 464 completion)

### 02-文生图适配层 ✅
- **输入**: Prompt "A cute cartoon cat on moon, sci-fi"
- **输出**: 生成图片URL并下载为1.75MB PNG
- **AI模型**: agnes-image-2.1-flash
- **图片URL**: `https://platform-outputs.agnes-ai.space/images/text-to-image/2026/06/daf5ab9c4bd94205af62a8b27f97c7c9.png`

### 03-文生音频适配层 ✅
- **输入**: "今天天气真好", 语音"冰糖"
- **输出**: WAV格式音频文件（从base64解码）
- **AI模型**: mimo-v2.5-tts
- **Token使用**: 144 tokens

---

## 关键修复

### 问题根因
`n8n HTTP Request V4.4` 节点在显式设置 `responseFormat: "json"` 时会自动开启 `useStream: true`，
导致下游 Code 节点收到 Node.js Readable Stream 对象而非解析后的 JSON。

### 解决方案
从 HTTP Request 节点的 `options` 中**移除** `responseFormat: "json"` 设置。
不显式设置时，n8n 默认返回解析后的 JSON 数据。

### 发现的问题
- `n8n_update_partial_workflow` 工具的 `updateNode` 操作在修改嵌套参数时会意外清空同级参数
- Task Runner 沙箱禁止 `child_process`，无法直接读取 `filesystem-v2` 引用
- 建议：修改 HTTP Request 节点时使用 `n8n_create_workflow` 完整重建

---

## 当前工作流ID映射

| 旧ID | 新ID | 名称 |
|------|------|------|
| `3b7UV45wtXmPZYvK` | `JjMxOUIMgJBpwxer` | 01-内容分析与分镜 |
| `3rnctg6HueWSWtxu` | `iD87BeQkqIZCLWiM` | 02-文生图适配层 |
| `KQ1kvg38eq3DgkIj` | `7aA8FNq2ixjuphuX` | 03-文生音频适配层 |
| `mmDE4qQKJHqdIZN7` | 不变 | 00-主编排（手动触发） |
| `MuNuZNCICl5kMqhQ` | 不变 | 04-视频合成 |

---

## 待办事项

1. **主编排工作流(00)** 需在 n8n UI 中手动触发（Manual Trigger），无法通过 API 激活
2. **视频合成工作流(04)** 需提供实际图片文件路径和音频文件路径进行端到端测试
3. **主编排工作流** 中的子工作流 webhook URL 指向的是旧 webhook ID，但因 webhook 路径相同（`storyboard`/`image-gen`/`tts-gen`），功能不变
