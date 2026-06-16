---
name: l3-rag
level: L3
category: AI多模型协作
requires: [l3-langchain, l2-file-processing, l2-database]
feeds_into: [l3-business-orchestration]
---

# L3-05 RAG 检索增强生成

## 概述

RAG (Retrieval-Augmented Generation) 是让 AI 回答基于你私有数据的最有效方式。不同于 Fine-tuning，RAG 不需要重新训练模型，而是将你的文档向量化存储，查询时检索最相关的片段作为上下文注入 Prompt。在 AIGC_Files 中，vectorStore 节点出现 45 次，documentLoader 出现 99 次。

## 适用场景

- 企业内部知识库问答（文档、Wiki、SOP）
- 客户支持机器人（基于产品手册回答）
- 法律/医疗专业问答（基于法规/文献）
- 个人文档助手（Notion 页面、Google Drive 文件）
- GitHub 代码库问答

## RAG 两阶段架构

### 阶段一：文档入库（Indexing）

```
[触发器]
  → Document Loader (加载文档)
  → Text Splitter (切分为 chunks)
  → Embeddings OpenAI (生成向量)
  → Vector Store (存储向量)
```

### 阶段二：查询检索（Query）

```
[用户提问]
  → Embeddings (将问题向量化)
  → Vector Store (检索最相关 chunks, topK=5)
  → AI Agent (基于检索结果回答)
    Prompt: "根据以下上下文回答用户问题：
             {context}
             ---
             问题：{query}"
  → [返回答案]
```

## 节点组合模板

### Google Drive → Qdrant RAG

```
Manual Trigger
  → Google Drive (读取指定文件夹中的文档)
  → SplitOut (逐文件处理)
    → Document Loader (加载文档)
    → Text Splitter (chunkSize: 800, overlap: 100)
    → Embeddings OpenAI (text-embedding-3-small)
    → Vector Store Qdrant (upsert)
```

### Notion → Supabase RAG

```
Schedule Trigger (每天同步)
  → Notion (获取数据库页面)
  → Filter (过滤未处理页面)
  → Document Loader
  → Text Splitter
  → Embeddings OpenAI
  → Supabase (存储向量 + 元数据)
```

### 智能检索对话 Bot

```
Telegram Trigger (用户提问)
  → Embeddings OpenAI (问题向量化)
  → Vector Store (检索 Top 5 chunks)
  → AI Agent
    System: "你是知识库助手。仅基于提供的文档上下文回答。
             如果上下文不足以回答，诚实告知用户。"
    User:   "上下文：{{ $json.chunks }}
             问题：{{ $('Telegram Trigger').item.json.message.text }}"
  → Telegram (回复答案 + 引用来源)
```

### Google RAG with MCP（无需自建向量库）

n8n MCP Client 可连接 Google File Search Store，实现零配置 RAG：

```
阶段 1 - 创建搜索空间:
  HTTP Request
    POST https://generativelanguage.googleapis.com/v1beta/fileSearchStores
    auth: httpQueryAuth (Google Studio API Key)
    body: { displayName: "空间名称" }

阶段 2 - 上传文件:
  Form Trigger (file upload)
    → HTTP Request
        POST /upload/v1beta/{空间名称}:uploadToFileSearchStore
        contentType: "binaryData"
        inputDataFieldName: "File"

阶段 3 - 查询:
  AI Agent (通过 MCP Client 连接到 Google File Search)
    → 自然语言提问
    → Google 自动检索文件内容
    → 返回带引用的答案
```

**优势**：无需搭建向量数据库、无需 Embedding 计算、文件变更自动同步、自带 MCP 工具调用。

## 参考工作流

| 文件 | RAG 模式 | 向量存储 |
|------|---------|----------|
| `workspaces/Filter/1414_Filter_Summarize_Automation_Triggered.json` | Notion → Supabase | Supabase |
| `workspaces/Splitout/1627_Splitout_Code_Automation_Triggered.json` | Google Drive → Pinecone | Pinecone |
| `workspaces/Manual/0933_Manual_Stickynote_Create_Webhook.json` | Bright Data → Pinecone | Pinecone |
| `workspaces/Telegram/1185_Telegram_Wait_Automate_Webhook.json` | Google Drive + Gemini → Qdrant | Qdrant |
| **`Workflow/ xiaolin/Google RAG Workflow with MCP.json`** | **Google File Search + MCP（零向量库）** | **Google** |

## 常见问题与经验

1. **Chunk 策略**：句义完整优先（按句子/段落边界切分），overlap 设置 10-20% 防止关键信息被截断
2. **检索质量**：topK 太小遗漏关键信息，太大引入噪音。一般 3-10 个 chunk，根据文档类型调整
3. **Embedding 成本**：OpenAI embedding 按 Token 计费，大规模索引用 batch API 降低成本
4. **增量更新**：文档变化时需要增量 upsert 而非全量重建索引
5. **引用溯源**：在 Prompt 中要求 AI 引用来源文档/页码，便于用户验证
6. **多语言支持**：embedding 模型对英文支持最好，中文内容检索效果可能略逊，考虑用专门的 multilingual embedding

## 升级路径

- 多数据源统一检索 → 学习 **[L3-06 多模型协作与路由]()**
- 企业级全流程 → 学习 **[L3-08 业务全流程编排]()**
