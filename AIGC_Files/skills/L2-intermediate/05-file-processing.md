---
name: l2-file-processing
level: L2
category: 数据处理与API集成
requires: [l2-http-api]
feeds_into: [l3-ai-text-gen, l3-ai-image-gen, l3-rag]
---

# L2-05 文件处理

## 概述

n8n 支持丰富的文件操作：PDF/图片提取文本、JSON/CSV 转换、二进制文件读写。在 AI 场景中，文件处理是将非结构化数据（PDF、图片）转化为 AI 模型可理解格式的关键桥梁。AIGC_Files 中 extractFromFile 出现 114 次，convertToFile 出现 69 次。

## 适用场景

- PDF 发票/简历文本提取 + AI 分析
- 图片转 Base64 供 Gemini Vision API 分析
- AI 生成的 JSON → CSV/Excel 文件下载
- AI 图片生成结果 → 文件格式转换与存储
- 大文件分片处理

## 核心节点速览

| 节点 | 功能 | 典型使用 |
|------|------|----------|
| `extractFromFile` | 从 PDF/图片/文档提取文本 | PDF → 文本 → AI 摘要 |
| `convertToFile` | JSON/文本 → 文件 | AI 结果 → CSV 下载 |
| `readBinaryFiles` | 读取二进制文件 | 图片/音频 → Base64 |
| `writeBinaryFile` | 保存二进制数据 | 图片/音频文件落盘 |
| `readWriteFile` | 文本文件读写 | 日志/TXT/代码文件 |
| `spreadsheetFile` | Excel 文件处理 | CSV/XLSX 导入导出 |

## 节点组合模板

### PDF 数据提取 + AI 分析

```
Webhook (上传 PDF)
  → extractFromFile (提取文本)
  → AI Agent (Gemini/OpenAI 分析内容)
  → Google Sheets (存储结构化结果)
```

### AI 图像生成 + 文件存储

```
Form Trigger (Prompt 输入)
  → HTTP Request (OpenAI DALL-E / Midjourney API)
  → convertToFile (Base64 → Binary Image)
  → Google Drive (存储图片)
  → Form (返回图片下载)
```

### CSV 报告生成

```
AI Agent (批量数据摘要)
  → Set (格式化为 CSV 结构)
  → convertToFile (JSON → CSV)
  → Email/Slack/Telegram (发送文件)
```

## 参考工作流

| 文件 | 文件处理模式 |
|------|-------------|
| `workflows/Extractfromfile/1444_Extractfromfile_Converttofile_Automation_Webhook.json` | PDF + Gemini 提取 → CSV |
| `workflows/Extractfromfile/1501_Extractfromfile_Form_Automate_Triggered.json` | 简历 PDF → AI 审阅 |
| `workflows/Form/1316_Form_Stickynote_Automation_Webhook.json` | Base64 → Binary Image 转换 |
| `workflows/Manual/1105_Manual_Stickynote_Automation_Webhook.json` | Text-to-Speech 音频输出 |

## 常见问题与经验

1. **文件大小限制**：n8n 默认最大 payload 为 16MB，大文件需分片处理或使用外部存储 URL
2. **编码问题**：中文 PDF 提取可能出现乱码，建议先用 ChatGPT/Gemini 测试目标文件的可提取性
3. **Base64 格式**：convertToFile 的 `sourceProperty` 指向 JSON 中的 Base64 字符串路径，如 `data[0].b64_json`
4. **Google Drive 集成**：生成的文件可保存到 Google Drive（`googleDrive` 节点），方便团队共享
5. **临时文件**：n8n 执行完毕后临时文件会被清理，需要持久化时存到 Drive 或下载

## 升级路径

- 提取的文本需要 AI 理解 → 学习 **[L3-01 AI 文本生成]()**
- 图片内容分析 → 学习 **[L3-02 AI 图像生成]()**（Vision API）
- 构建知识库 → 学习 **[L3-05 RAG 检索增强生成]()**
