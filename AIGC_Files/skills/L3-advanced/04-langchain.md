---
name: l3-langchain
level: L3
category: AI多模型协作
requires: [l3-ai-text-gen, l3-ai-agent]
feeds_into: [l3-rag, l3-multi-model]
---

# L3-04 LangChain 链式编排

## 概述

LangChain 节点为 n8n 带来了结构化的 LLM 编排能力。不同于简单的单次调用，LangChain 支持文档加载器、文本分割器、向量存储、链式调用、输出解析器等高级模式。在 AIGC_Files 中，chainLlm 出现 191 次，outputParserStructured 出现 154 次。

## 适用场景

- 结构化输出（强制 JSON Schema）
- 多文档 RAG 系统
- 多步推理链（Chain of Thought）
- LLM 输出质量控制
- 自定义检索器与加载器

## LangChain 节点生态

| 节点 | 功能 | 典型使用 |
|------|------|----------|
| `chainLlm` | LLM 链式调用 | 多步推理管道 |
| `outputParserStructured` | 结构化输出解析 | JSON Schema 约束 |
| `textSplitter` | 文本切分 | 文档分块 (Chunking) |
| `documentLoader` | 文档加载 | PDF/HTML/Markdown 导入 |
| `vectorStore` | 向量存储与检索 | Qdrant/Pinecone 集成 |
| `informationExtractor` | 信息提取 | 实体/关系抽取 |
| `textClassifier` | 文本分类 | 意图识别/情感分析 |
| `chainSummarization` | 摘要链 | 长文本摘要 |

## 节点组合模板

### 结构化输出链

```
Manual Trigger (输入文本)
  → OpenAI Chat Model (gpt-4o-mini)
  → Chain LLM (处理文本)
  → Output Parser Structured (强制 JSON 输出)
    Schema: {
      "title": "string",
      "summary": "string",
      "keywords": ["string"],
      "sentiment": "positive|negative|neutral",
      "confidence": "number"
    }
  → Set (使用解析后的结构化数据)
```

### RAG 文档处理链

```
Webhook (上传文档 URL)
  → Document Loader (加载文档)
  → Text Splitter (切分为 chunks, chunkSize: 1000)
  → Embeddings OpenAI (生成向量)
  → Vector Store Qdrant (存储向量)
  → Chain LLM + Retriever (检索增强生成)
```

### 信息提取链

```
Webhook (上传简历 PDF)
  → Extract from File (提取文本)
  → Information Extractor
    Schema: {
      "name": "...",
      "skills": [...],
      "experience": [...],
      "education": [...]
    }
  → Google Sheets (结构化存储)
```

## 参考工作流

| 文件 | LangChain 模式 |
|------|---------------|
| `workflows/Manual/1285_Manual_Stickynote_Import_Triggered.json` | Workflow Retriever 示例 |
| `workflows/Manual/1397_Manual_Stickynote_Automation_Triggered.json` | Code Node 示例 |
| `workflows/Manual/1457_Manual_Stickynote_Process_Triggered.json` | Output Parser 示例 |
| `workflows/Splitout/1627_Splitout_Code_Automation_Triggered.json` | 上下文感知分块 RAG |
| `workflows/Stickynote/2023_Stickynote_Create_Triggered.json` | 自定义 AI Agent + LangChain |

## 常见问题与经验

1. **Chunk Size 调优**：文档分块大小影响检索质量，一般 500-1000 tokens；太小丢失上下文，太大检索精度下降
2. **JSON Schema 容错**：即使使用 Structured Output，LLM 仍可能偶尔输出不合法 JSON，添加 Code 节点做格式校验
3. **Embedding 模型选择**：`text-embedding-3-small`（成本低）vs `text-embedding-3-large`（精度高），根据预算和精度需求选择
4. **向量存储选型**：Qdrant（开源自托管）、Pinecone（免运维云服务）、Supabase（PG 内置向量）
5. **节点版本**：LangChain 节点 typeVersion 更新频繁，推荐使用最新版本

## 升级路径

- 文档检索 + AI 回答 → 学习 **[L3-05 RAG 检索增强生成]()**
- 多模型链式调用 → 学习 **[L3-06 多模型协作与路由]()**
