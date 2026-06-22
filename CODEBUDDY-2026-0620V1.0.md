# CODEBUDDY.md — N8N-Demo03 项目指导

> AI 是工作流的构建者，不是理论顾问。所有操作必须通过 MCP 工具执行。

---

## 排障速查（最先看）

| 文档 | 用途 |
|------|------|
| **[`docs/project-memory-and-troubleshooting.md`](./docs/project-memory-and-troubleshooting.md)** | 架构全景、工作流清单、已知错误模式、排障流程 |
| **[`docs/n8n-stream-fix-guide.md`](./docs/n8n-stream-fix-guide.md)** | HTTP Request → Code 节点 Stream 修复专项 |

**诊断口诀**：`n8n_executions(mode='error')` → 看 `upstreamContext` → 找 `_readableState`（Stream 问题）或用错误消息匹配已知模式。

**构建口诀**：`search_nodes` → `get_node(info)` → `validate_node` → `n8n_create/update` → `n8n_validate` → `curl` 测试。

---

## 环境与基础设施

### n8n 实例

| 属性 | 值 |
|------|-----|
| 地址 | `http://localhost:7890` |
| 版本 | n8n v2.5.0，Docker 部署（Task Runner 沙箱） |
| API 认证 | 环境变量 `N8N_API_URL` + `N8N_API_KEY` |
| MCP 连接 | `n8n_health_check` 验证 |

### Docker 拓扑

```
n8n-demo03 (7890:5678) ──┐
                          ├── n8n-network ──┐
n8n-composer (8899:8899) ─┘                 │
                                             │
共享卷: ./n8n-files → /files                │
外部 API: agnes-ai, xiaomimimo, openai ─────┘
```

### 关键配置

```yaml
# docker-compose.yml 关键项
NODE_FUNCTION_ALLOW_EXTERNAL=*    # Code 节点可用 require
N8N_PAYLOAD_SIZE_MAX=64           # 64MB 上限
EXECUTIONS_DATA_PRUNE_ENABLED=true # 自动清理（7天）

# API Keys（必须在 docker-compose.yml 显式声明，仅 .env 不够）
AGNES_API_KEY=${AGNES_API_KEY}
MIMO_API_KEY=${MIMO_API_KEY}
OPENAI_API_KEY=${OPENAI_API_KEY}
OPENAI_BASE_URL=${OPENAI_BASE_URL:-https://apihub.agnes-ai.com/v1}
```

---

## 工具体系（精简版）

### MCP 工具分类

| 类别 | 核心工具 | 备注 |
|------|----------|------|
| **发现** | `search_nodes`、`search_templates` | 先搜后建 |
| **查询** | `get_node`（mode: info/docs/search_properties） | 渐进式：minimal→standard→full |
| **验证** | `validate_node`、`validate_workflow` | 交付前必须通过 |
| **CRUD** | `n8n_create/list/get/update/delete` | `update_partial` 最常用 |
| **运行** | `n8n_test_workflow`、`n8n_executions` | 测试+排障 |
| **审计** | `n8n_audit_instance`、`n8n_workflow_versions` | 安全+回滚 |

> 完整文档调用 `tools_documentation(topic="工具名", depth="full")`

### ⚠️ nodeType 格式陷阱（必读）

| 工具类别 | 格式 | 示例 |
|----------|------|------|
| 搜索/验证（`search_nodes`、`get_node`、`validate_node`） | 短前缀 | `nodes-base.httpRequest` |
| 工作流管理（`n8n_create`、`n8n_update` 等） | 全前缀 | `n8n-nodes-base.httpRequest` |

### 标准构建循环

```
search_nodes → get_node(info) → validate_node → n8n_create_workflow
    → n8n_validate_workflow → n8n_update_partial_workflow → curl 测试
```

### Skills 按需加载

| Skill | 触发场景 |
|-------|----------|
| `n8n-mcp-tools-expert` ⭐ | 工具选择、nodeType 格式、验证 profile |
| `n8n-node-configuration` | 操作感知配置、属性依赖 |
| `n8n-code-javascript` | Code 节点开发 |
| `n8n-expression-syntax` | `{{}}` 表达式 |
| `n8n-validation-expert` | 验证错误解读 |
| `n8n-workflow-patterns` | 五大架构模式 |

---

## 构建规范

### 质量标准（交付前检查）

- [ ] 所有节点通过 `validate_node`（profile: `runtime`）
- [ ] 工作流通过 `n8n_validate_workflow`
- [ ] 错误路径有 Error Trigger 或 `onError` 处理
- [ ] Code 节点返回 `[{json: {...}}]` 格式
- [ ] Webhook 节点用 `$input.first().json.body` 访问数据
- [ ] 通过 `curl` 实际触发测试

### 节点设计五原则

1. **渐进式发现**：`get_node` detail: minimal → standard → full
2. **操作感知**：不同 resource/operation 的必填字段不同
3. **依赖感知**：理解字段可见性与联动规则
4. **智能参数**：IF 节点 `branch: "true"/"false"`，Switch 节点 `case: 0/1`
5. **最小配置**：只配必填，渐进添加

### 命名规范

| 类别 | 格式 | 示例 |
|------|------|------|
| 工作流 | `[触发类型] 功能描述` | `[Webhook] 00-文生视频` |
| 节点 | 中文描述 | `解析分镜输出`、`调用AI生成分镜` |
| 节点 ID | kebab-case 英文 | `parse-scenes`、`call-ai` |
| Webhook 路径 | kebab-case | `text-to-video` |

### 验证 Profile 选择

| Profile | 场景 |
|---------|------|
| `ai-friendly` | 开发初期（减少误报） |
| `runtime` | ⭐ 预部署推荐 |
| `strict` | 最终交付 |
| `minimal` | 快速探索 |

### 错误处理机制

- Error Trigger 节点捕获工作流级错误
- HTTP Request 设置 `onError: "continueRegularOutput"` 防中断
- IF/Switch 必须覆盖所有分支
- 关键节点考虑 `continueOnFail: true`

---

## Code 节点速查

| 类型 | 返回格式 | 数据访问 | 禁区 |
|------|---------|---------|------|
| JavaScript | `[{json: {...}}]` | `$input`、`$json` | 禁用 `{{}}` 表达式 |
| Python | `[{json: {...}}]` | `_input`、`_json` | 无第三方库 |
| Code Tool (AI Agent) | **字符串** | `query` | 无 `$input`/`$helpers`/`$fromAI` |

### Task Runner 沙箱可用性

| ✅ 可用 | ❌ 不可用 |
|---------|-----------|
| `Buffer`、`console.log` | `$helpers.httpRequest()` |
| `$input`、`$json`、`$node` | `fetch()` |
| `JSON`、`Date`、`Math` | `require()`（`NODE_FUNCTION_ALLOW_EXTERNAL=*` 后可用） |
| String/Array 标准方法 | 第三方 npm 包（需白名单） |

### ⚠️ Stream 问题（最高频陷阱）

HTTP Request V4.4 → Code 节点：下游收到 Node.js Readable Stream 对象而非 JSON。修复参见 [`docs/n8n-stream-fix-guide.md`](./docs/n8n-stream-fix-guide.md)。

---

## AI 协作准则

1. **工具优先**：所有 n8n 操作通过 MCP 工具，禁止纯理论输出
2. **先搜后建**：`search_nodes` + `search_templates` 确认可用资源
3. **先验后改**：配置必须 `validate_node` 通过后才提交
4. **增量迭代**：用 `n8n_update_partial_workflow`，避免全量替换
5. **安全第一**：凭证用 Credential 管理，不硬编码；编辑前备份；用 `n8n_workflow_versions` 追踪变更
6. **激活提醒**：交付后提醒用户手动激活（API 不支持）
