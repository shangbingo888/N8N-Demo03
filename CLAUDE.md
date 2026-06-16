# N8N-Demo03: AI 驱动的 n8n 工作流构建项目

## 项目定位

本项目利用 AI 结合 n8n MCP 服务端与 n8n 工具集，在 n8n 实例中直接搭建、验证、部署高质量工作流。AI 是工作流的实际构建者，而非理论顾问——所有操作必须通过工具直接作用于 n8n 实例。

---

## 核心目标

1. **直接操作优先**：AI 必须通过 MCP 工具和 Skill 与 n8n 交互，禁止仅输出 JSON 或理论指导而不执行
2. **迭代式构建**：遵循 search -> get_node -> configure -> validate -> create -> validate 循环，每次修改后验证
3. **质量内建**：每个工作流交付前必须通过节点级和工作流级双重验证
4. **可维护性**：工作流结构清晰、命名规范、错误处理完备，便于后续维护

---

## 可用工具体系

### 一、n8n MCP 服务端工具（40+ 工具）

需要 `N8N_API_URL` + `N8N_API_KEY` 环境变量才能调用 API 类工具。通过 `/n8n-mcp-tools-expert` Skill 获取完整文档。

#### 节点发现工具

| 工具 | 用途 | 成功率 |
|------|------|--------|
| `search_nodes` | 按关键词搜索节点（1,851 个节点，265 个 AI 工具变体） | 99.9% |
| `get_node` | 统一节点查询（mode: `info`/`docs`/`search_properties`/`versions`/`compare`/`breaking`/`migrations`） | 91.7% |
| `list_nodes` | 按分类列出节点 | 99.6% |
| `list_node_templates` | 按节点类型查找模板 | - |

#### 配置验证工具

| 工具 | 用途 |
|------|------|
| `validate_node` | 统一节点验证（mode: `minimal`/`full`，profile: `minimal`/`runtime`/`ai-friendly`/`strict`） |
| `validate_workflow` | 工作流结构验证 |
| `get_property_dependencies` | 查看字段依赖关系 |

#### 工作流管理工具（需 n8n API）

| 工具 | 用途 | 成功率 |
|------|------|--------|
| `n8n_create_workflow` | 创建新工作流 | 96.8% |
| `n8n_update_partial_workflow` | 增量修改工作流（15 种操作类型，最常用） | 99.0% |
| `n8n_update_full_workflow` | 整体替换工作流 | - |
| `n8n_delete_workflow` | 删除工作流 | - |
| `n8n_validate_workflow` | 验证已存储的工作流 | 99.7% |
| `n8n_test_workflow` | 测试工作流执行 | - |
| `n8n_get_workflow` | 获取完整工作流 JSON | - |
| `n8n_get_workflow_structure` | 获取节点与连接（不含参数） | - |
| `n8n_get_workflow_minimal` | 获取 ID、名称、状态、标签（快速） | - |
| `n8n_list_workflows` | 列出工作流（支持按状态/标签过滤） | - |
| `n8n_audit_instance` | 审计实例配置与健康状态 | - |
| `n8n_manage_credentials` | 凭证管理（CRUD，安全加密存储） | - |
| `n8n_deploy_template` | 从模板库部署工作流 | - |
| `n8n_autofix_workflow` | 自动修复工作流问题 | - |
| `n8n_workflow_versions` | 版本管理与回滚 | - |
| `n8n_list_executions` | 查看执行历史 | - |
| `n8n_get_execution` | 获取单次执行详情 | - |
| `n8n_trigger_webhook_workflow` | 触发 Webhook 工作流测试 | - |

#### 模板与文档工具

| 工具 | 用途 |
|------|------|
| `search_templates` | 搜索 2,352 个模板（支持 by_nodes/by_task/by_metadata 模式） |
| `get_template` | 获取模板详情（mode: `structure`/`full`/`metadata`） |
| `get_database_statistics` | 查看节点/模板统计数据 |
| `tools_documentation` | 获取工具文档 |
| `n8n_health_check` | 检查 MCP 服务端连通性 |

### 二、n8n 工具集（8 个 Skill）

| Skill | 用途 | 调用方式 |
|-------|------|----------|
| `n8n-mcp-tools-expert` | MCP 工具使用指南和最佳实践 | `/n8n-mcp-tools-expert` |
| `n8n-workflow-patterns` | 5 种核心工作流架构模式 | `/n8n-workflow-patterns` |
| `n8n-node-configuration` | 节点操作感知配置指南 | `/n8n-node-configuration` |
| `n8n-expression-syntax` | n8n 表达式语法规范 | `/n8n-expression-syntax` |
| `n8n-code-javascript` | JavaScript Code 节点开发 | `/n8n-code-javascript` |
| `n8n-code-python` | Python Code 节点开发 | `/n8n-code-python` |
| `n8n-code-tool` | AI Agent 可调用的自定义 Code Tool 开发 | `/n8n-code-tool` |
| `n8n-validation-expert` | 验证错误解读与修复 | `/n8n-validation-expert` |

### 三、工具协作流程

标准构建流程：

```
1. n8n-mcp-tools-expert    → 确定工具选择策略
2. n8n-workflow-patterns    → 选择架构模式
3. search_nodes             → 发现所需节点（1,851 节点，265 AI 工具变体）
4. get_node (mode: info)    → 了解节点配置与必填字段
5. n8n-node-configuration   → 配置节点参数
6. validate_node (full)     → 验证节点配置
7. n8n_create_workflow      → 创建工作流
8. n8n_validate_workflow    → 验证工作流
9. n8n_update_partial_workflow → 迭代修改（15 种操作类型）
10. n8n-validation-expert   → 修复验证错误
```

---

## 工作流构建规范

### 质量标准

- 所有节点配置必须通过 `validate_node`（mode: full, profile: runtime）验证
- 工作流创建后必须通过 `n8n_validate_workflow` 验证
- 错误处理节点覆盖所有可能失败路径
- 节点命名清晰、无歧义
- Webhook 类工作流必须处理 `$json.body` 数据结构

### 节点设计原则

1. **渐进式发现**：`get_node` mode:info -> 必要时 mode:search_properties -> 按需 mode:docs
2. **操作感知**：不同 resource/operation 组合需要不同字段，不要假设配置可移植
3. **依赖感知**：使用 `get_property_dependencies` 理解字段可见性规则
4. **善用智能参数**：IF 节点用 `branch: "true"/"false"`，Switch 节点用 `case: 0/1`
5. **AI 连接类型**：使用 `sourceOutput` 指定连接类型（ai_languageModel、ai_tool、ai_memory 等 8 种）
6. **最小化配置**：只配置必填字段，渐进式添加可选字段

### nodeType 格式规范

**两类工具使用不同格式**：

```
搜索/验证工具: "nodes-base.slack"        ← 短前缀
工作流工具:    "n8n-nodes-base.slack"    ← 全前缀
```

`search_nodes` 返回两种格式，注意区分使用场景。

### 错误处理机制

- 使用 Error Trigger 节点捕获工作流错误
- 关键节点设置 `continueOnFail` 防止单点失败中断整个流程
- HTTP 请求配置重试机制
- 数据库操作使用事务保护
- IF/Switch 节点处理异常分支

### 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| 工作流名称 | `[触发类型] 功能描述` | `[Webhook] Slack 消息通知` |
| 节点名称 | 描述性名称，反映节点职责 | `查询用户数据`、`发送通知` |
| 节点 ID | 使用有意义的标识符 | `webhook-trigger`、`slack-notify` |
| 路径/Webhook | kebab-case | `form-submit`、`github-webhook` |

---

## AI 协作准则

### 必须遵守

1. **工具优先**：所有 n8n 操作必须通过 MCP 工具执行，不输出脱离工具的"示例 JSON"
2. **先搜后建**：构建前必须搜索节点和模板，确认可用节点和最佳实践
3. **先验后建**：节点配置必须验证后才能提交到工作流
4. **迭代修改**：使用 `n8n_update_partial_workflow` 增量修改，不要一次构建完整工作流
5. **激活提醒**：工作流创建后提醒用户在 n8n UI 中手动激活（API 不支持激活）

### 模板库复用

构建前搜索模板库（`search_templates`，支持 by_nodes/by_task/by_metadata 模式），复用已有模式而非从零开始。模板库包含 2,352 个真实工作流模板。

### 五大核心模式

1. **Webhook 处理**：接收请求 -> 校验 -> 转换 -> 响应/通知
2. **HTTP API 集成**：触发 -> HTTP 请求 -> 转换 -> 操作 -> 错误处理
3. **数据库操作**：调度 -> 查询 -> 转换 -> 写入 -> 验证
4. **AI Agent 工作流**：触发 -> AI Agent (模型 + 工具 + 记忆) -> 输出
5. **定时任务**：调度 -> 获取 -> 处理 -> 交付 -> 日志

### 验证 Profile 选择

| Profile | 场景 |
|---------|------|
| `minimal` | 快速检查必填字段（宽松，适合早期探索） |
| `runtime` | 值与类型验证（推荐预部署使用） |
| `ai-friendly` | 减少 AI 配置误报 |
| `strict` | 生产环境最大验证 |

---

## 部署与安全

### MCP 服务端部署选项

| 方式 | 说明 |
|------|------|
| Dashboard 托管 | dashboard.n8n-mcp.com（推荐快速开始） |
| Docker | 容器化部署，支持自定义配置 |
| Railway | 一键云部署 |
| npm | 本地安装，适合开发环境 |

传输模式：stdio（本地）、SSE、streamable HTTP（远程）。

### 安全注意事项

- **凭证安全**：`n8n_manage_credentials` 加密存储凭证，绝不硬编码
- **生产环境**：对生产实例操作前确认范围，避免误改活跃工作流
- **测试优先**：使用 `n8n_test_workflow` 验证后再激活
- **版本控制**：使用 `n8n_workflow_versions` 追踪变更，支持回滚

---

## 环境要求

- n8n 实例地址和 API Key 配置在环境变量中（`N8N_API_URL` + `N8N_API_KEY`）
- MCP 服务端连接正常（使用 `n8n_health_check` 验证）
