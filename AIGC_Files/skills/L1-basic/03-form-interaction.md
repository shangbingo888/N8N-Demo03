---
name: l1-form-interaction
level: L1
category: 触发与响应
requires: []
feeds_into: [l2-http-api, l3-ai-image-gen, l3-ai-text-gen]
---

# L1-03 表单交互

## 概述

Form Trigger 提供开箱即用的 Web 表单界面，让非技术用户也能通过可视化表单触发自动化流程。表单提交后可将结果以页面形式返回，支持文本、图像、文件下载等多种响应类型。是构建"AI 工具 Demo"最快捷的方式。

## 适用场景

- 快速搭建 AI 图像生成工具（输入 Prompt → 返回图片）
- 用户反馈收集与自动处理
- 内部工具：批量文本翻译、摘要生成
- 数据录入：信息收集后自动写入 Google Sheets
- AI 对话界面原型

## 输入定义（表单字段）

| 字段类型 | 说明 | n8n 配置 |
|----------|------|----------|
| Text | 文本输入（Prompt、关键词等） | `fieldType: "text"` |
| Dropdown | 下拉选择（模型、尺寸、风格等） | `fieldType: "dropdown"` + `fieldOptions.values[]` |
| Number | 数字输入 | `fieldType: "number"` |
| Date | 日期选择 | `fieldType: "date"` |
| **File** | **文件上传** | `fieldType: "file"` + `multipleFiles: false/true` |

提交后通过 `$json.{fieldLabel}` 访问表单字段值。文件字段通过 `$json.{fieldLabel}.fileName / fileSize / mimeType` 访问元信息。

## 输出定义

Form Trigger 输出用户填写的表单数据：

```
{
  "Prompt": "A cat wearing a hat",
  "Image size": "1024x1024"
}
```

使用 Form Completion 节点返回结果：

| 响应类型 | 说明 |
|----------|------|
| `returnText` | 返回纯文本 |
| `returnBinary` | 返回二进制文件（图片、PDF 等） |
| `completionMessage` | 自定义完成提示 |

## 节点组合模板

### AI 图像生成工具

```
Form Trigger (Prompt + Size 输入)
  → HTTP Request (调用 OpenAI/DALL-E API)
  → Convert to File (Base64 → Binary)
  → Form (返回图片供下载)
```

**关键参数映射**：
```
Form Trigger.fields → $json.Prompt, $json["Image size"]
HTTP Request.body.model → "gpt-image-1"
HTTP Request.body.prompt → ={{ $json.Prompt }}
Convert to File.sourceProperty → "data[0].b64_json"
Form.operation → "completion" + respondWith: "returnBinary"
```

### 海报生成器（Dropdown 多选风格）

```
Form Trigger
  ├─ 主标题 (text, required)
  ├─ 副标题 (text, required)
  ├─ 辅助信息 (text)
  └─ 海报风格 (dropdown: 手写/3D/极简/赛博朋克/复古/霓虹/扁平/涂鸦/书法/像素/自然)

  → Code (拼接风格关键词到 Prompt)
  → OpenAI (gpt-image-1, quality: high, size: 1024x1536)
  → Form Completion (返回海报)
```

### 文件上传表单

```
Form Trigger
  └─ File (file, required)

  → HTTP Request
      contentType: "binaryData"
      inputDataFieldName: "File"
      url: "https://api.example.com/upload"

  → Form Completion (返回上传结果)
```

**文件上传注意事项**：
- `inputDataFieldName` 必须与表单字段 Label 完全一致
- 上传大文件时调整 HTTP Request 的 timeout 配置
- 文件信息通过 `$json.{fieldLabel}.fileName` 获取

## 参考工作流

| 文件 | 说明 |
|------|------|
| `workflows/Form/1316_Form_Stickynote_Automation_Webhook.json` | OpenAI 图像生成器（经典模板） |
| `workflows/Form/1762_Form_Aggregate_Automation_Triggered.json` | SEO 博客生成器 |
| `workflows/Http/1535_HTTP_Form_Automate_Webhook.json` | 博客内容自动创建 |
| **`Workflow/ xiaolin/n8nposter.json`** | **海报生成器（11 种风格下拉）** |
| **`Workflow/ xiaolin/Google RAG Workflow with MCP.json`** | **文件上传表单 + Google Search Store** |
| **`Workflow/workflow.json`** | **表单→DeepSeek 搜索→播客生成** |

## 常见问题与经验

1. **字段命名**：表单字段 Label 会成为 `$json` 的 key，使用英文命名避免编码问题
2. **必填校验**：关键字段开启 `requiredField: true`
3. **文件大小**：返回大图片时可能超时，调整 executionTimeout
4. **样式定制**：Form Trigger 的界面样式有限，如需深度定制建议用 Webhook + 自定义前端

## 升级路径

- 添加 AI 能力 → 学习 **[L3-01 AI 文本生成]()** 或 **[L3-02 AI 图像生成]()**
- 表单数据持久化 → 学习 **[L2-04 Google Sheets 读写]()**
- 构建更复杂的交互 → 学习 **[L1-04 Telegram Bot 对话]()**
