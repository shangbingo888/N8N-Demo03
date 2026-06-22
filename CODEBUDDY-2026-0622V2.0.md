# CODEBUDDY.md

## 核心能力

### 1. 文生视频全链路流水线
```
用户文本输入 → AI 分镜脚本 → 文生图(Agnes) + TTS(Mimo) → FFmpeg 合成 → MP4 输出
```
- **触发方式**：`POST localhost:7890/webhook/text-to-video`
- **主工作流**：`S5r7jE8tY3UJa15j`（18 节点）| **合成服务**：`composer:8899`（Docker 内网）

### 2. AI 通过 MCP 构建 n8n 工作流
AI 是工作流的**构建者**，非理论顾问——通过 n8n MCP 工具直接创建、配置、验证、测试工作流。

---

## 开发工作流

> **新增工作流或功能需求时，严格遵循以下 5 步生命周期。所有操作通过 MCP 工具执行，禁止仅输出 JSON。**

### 1. 模板检索
优先搜索现有模板库，确认是否存在可复用的模板：
- **远程**：`search_nodes` → `search_templates` 搜索 n8n 官方模板
- **本地**：检查 `Workflow/` 目录下已导出的工作流 JSON

### 2. 本地开发
无论有无可用模板，均须先进行本地文件设计，通过静态验证后才提交：
- 在 `Workflow/` 中创建工作流 JSON 文件（节点定义 + 连接关系）
- `validate_node`（单节点）+ `n8n_validate_workflow`（全工作流）静态验证
- 复用模板时直接修改本地 JSON，而非在容器内边改边试

### 3. 容器集成
本地验证通过后，连接 Docker 容器集成调试：
- 优先用 `n8n_update_partial_workflow` 增量推送，而非整体替换
- `n8n_test_workflow` 验证实际运行效果
- **隔离原则**：避免直接在运行容器中反复修改，防止环境污染

### 4. 同步更新
远程调试完成后，必须将最终版本同步回本地：
- `n8n_get_workflow` 导出容器中最新的工作流定义
- 保存到 `Workflow/` 目录，覆盖初始本地版本

### 5. 故障归档
调试遇到的问题必须写入知识库：
- 目标文件：`docs/project-memory-and-troubleshooting.md`
- 记录：错误现象 → 根因分析 → 修复方案 → 受影响节点
- 同步更新决策记录和变更日志，避免重复踩坑

### 工具链速查
```
search_nodes → get_node(mode:'info') → validate_node(mode:'full')
→ n8n_create_workflow → n8n_validate_workflow
→ n8n_update_partial_workflow → n8n_test_workflow
```

> 交付后提醒用户在 n8n UI 手动激活工作流。

---

## 文档索引（排障先看这里）

| 文档 | 内容 |
|------|------|
| [`docs/project-memory-and-troubleshooting.md`](./docs/project-memory-and-troubleshooting.md) | **项目大脑**：架构全景、工作流清单、API 依赖、已知错误模式及修复（含 Stream 问题完整方案，见 2.2.1 节） |

---

## 致命陷阱卡

### nodeType 格式不可混用
| 工具类别 | 格式 | 示例 |
|----------|------|------|
| search_nodes / get_node / validate_node | **短前缀** | `nodes-base.httpRequest` |
| n8n_create / n8n_update / n8n_validate | **全前缀** | `n8n-nodes-base.httpRequest` |

### HTTP Request → Code 节点 Stream 问题（最高频）
Docker Task Runner 下，HTTP Request V4.4 下游 Code 节点收到的是 `Readable Stream`，不是 JSON。
```
诊断：n8n_executions(mode='error') → 看 upstreamContext 有 _readableState → 确认
修复：_outBuffer + lastIndexOf('}') 截断 → 详见 project-memory 2.2.1 节
```

### Code 节点三大契约
| 类型 | 返回格式 | 数据访问 | 禁区 |
|------|---------|---------|------|
| JS Code 节点 | `[{json: {...}}]` | `$input` / `$json` / `$node` | 禁用 `{{}}` 表达式；Task Runner 下无 `$helpers.httpRequest()` / `fetch()` |
| Python Code 节点 | `[{json: {...}}]` | `_input` / `_json` / `_node` | 无第三方库（无 requests/pandas） |
| Code Tool (AI Agent) | **字符串** `JSON.stringify()` | `query` / `_query` | 无 `$input` / `$helpers` / `$fromAI()` / 状态保持 |

### Webhook body 陷阱
Webhook 数据在 `$input.first().json.body`，**不是** `$json.body`。

---

## 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| 工作流名 | `[触发类型] 功能描述` | `[Webhook] 文生视频` |
| 节点名 | 中文描述 | `AI分镜生成`、`TTS音频` |
| 节点 ID | 英文 kebab-case | `webhook-trigger`、`slack-notify` |

---

## 安全红线

> **绝不直接编辑生产工作流！** 先复制 → 开发环境测试 → 导出备份 → 验证 → 再部署。
> 凭证通过 `n8n_manage_credentials` 管理，绝不硬编码到工作流 JSON。

---

## 环境速查

- **n8n 实例**：`localhost:7890`（容器 `n8n-demo03`，内部端口 5678）
- **合成服务**：`composer:8899`（容器 `n8n-composer`，Docker 内网）
- **API 依赖**：Agnes AI/Image（`apihub.agnes-ai.com`）、Mimo TTS（`api.xiaomimimo.com`）、OpenAI 兼容 API
- **共享存储**：`n8n-files:/files`（两个容器共享，视频/图片输出目录）
- **关键环境变量**：`N8N_API_URL` / `N8N_API_KEY` | `NODE_FUNCTION_ALLOW_EXTERNAL=*`（允许 Code 节点 require）
