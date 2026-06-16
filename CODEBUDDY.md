# CODEBUDDY.md This file provides guidance to CodeBuddy when working with code in this repository.

## 项目核心目标

本项目的定位是**借助 AI 在 n8n 中构建高质量工作流**——AI 是工作流的实际构建者，而非理论顾问。

1. **直接操作优先**：AI 必须通过 MCP 工具和 Skill 与 n8n 实例交互，禁止仅输出 JSON 或理论指导而不执行
2. **迭代式构建**：遵循 `search → get_node → configure → validate → create → validate` 的循环流程，每次修改后验证
3. **质量内建**：每个工作流交付前必须通过节点级（`validate_node`）和工作流级（`n8n_validate_workflow`）双重验证
4. **可维护性**：工作流结构清晰、命名规范、错误处理完备，便于后续迭代与团队协作

---

## 可用工具体系

### 一、n8n MCP 服务端（v2.57.3）

仓库地址：https://github.com/czlonkowski/n8n-mcp

**数据覆盖**：1,851 个节点（822 核心 + 1,029 社区，911 已验证）| 2,352 个模板（AI 元数据覆盖 99.96%）| 156 个真实配置示例 | 265 个 AI 工具变体

所有 API 类工具依赖 `N8N_API_URL` + `N8N_API_KEY` 环境变量。通过 `n8n-mcp-tools-expert` Skill 获取完整使用文档。

#### 核心工具（无需 n8n API，7 个）

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `search_nodes` | 全文搜索节点 | `source: 'community'\|'verified'` 筛选、`includeExamples: true` 获取示例配置 |
| `get_node` | **统一多模式节点查询** | `mode: 'info'`（detail: minimal/standard/full）、`'docs'`（Markdown 文档）、`'search_properties'`、`'versions'`、`'compare'`、`'breaking'`、`'migrations'` |
| `validate_node` | 节点配置验证 | `mode: 'minimal'` 快速检查 / `'full'` 全面验证，profile: minimal/runtime/ai-friendly/strict |
| `validate_workflow` | 完整工作流验证 | 含连接、表达式、AI Agent 校验 |
| `validate_workflow_connections` | 工作流连接结构检查 | 验证节点间连接的正确性 |
| `validate_workflow_expressions` | n8n 表达式校验 | 检查模板表达式的有效性 |
| `tools_documentation` | 获取任意 MCP 工具文档 | 建议优先调用此工具了解其他工具的用法 |

#### 模板工具（无需 n8n API，2 个）

| 工具 | 用途 | 关键参数 |
|------|------|----------|
| `search_templates` | 搜索 2,352 个模板 | 四种模式：`keyword`（默认全文）、`by_nodes`（按节点类型）、`by_task`（按任务类型如 webhook_processing）、`by_metadata`（按复杂度/目标用户/所需服务） |
| `get_template` | 获取模板详情 | `mode: 'nodes_only'` / `'structure'` / `'full'` |

#### 工作流管理工具（需 n8n API，13 个）

**工作流 CRUD**：

| 工具 | 用途 |
|------|------|
| `n8n_create_workflow` | 创建包含节点和连接的新工作流 |
| `n8n_get_workflow` | 获取工作流，mode: `full` / `details` / `structure` / `minimal` |
| `n8n_update_partial_workflow` | ⭐增量修改（最常用），支持 add/remove/update node、add/remove connection、cleanStaleConnections 等操作 |
| `n8n_update_full_workflow` | 完整替换工作流定义 |
| `n8n_delete_workflow` | 永久删除工作流 |
| `n8n_list_workflows` | 列出工作流，支持过滤和分页 |

**验证与修复**：

| 工具 | 用途 |
|------|------|
| `n8n_validate_workflow` | 按 ID 在实例中校验工作流 |
| `n8n_autofix_workflow` | 自动修复常见工作流配置错误 |
| `n8n_test_workflow` | 测试/触发工作流（支持 webhook、表单、聊天触发） |

**运行与审计**：

| 工具 | 用途 |
|------|------|
| `n8n_executions` | 执行管理：`list` / `get` / `delete` 三种操作 |
| `n8n_manage_credentials` | 凭证管理：list / get / create / update / delete / getSchema |
| `n8n_audit_instance` | 安全审计——结合 n8n 内置审计 API 与深度工作流扫描 |
| `n8n_deploy_template` | 从 n8n.io 部署模板到实例，自动修复兼容问题 |
| `n8n_workflow_versions` | 版本历史管理与一键回滚 |
| `n8n_health_check` | 检查 n8n API 连接状态与功能可用性 |

### 二、n8n Skills（8 个技能）

仓库地址：https://github.com/czlonkowski/n8n-skills | 安装方式：`/plugin install czlonkowski/n8n-skills`

技能通过语义匹配自动激活，复杂任务会多技能协同组合。

| Skill | 核心知识 | 关键陷阱与警告 |
|-------|---------|---------------|
| **`n8n-mcp-tools-expert`** ⭐最高优先级 | 工具选择策略；nodeType 格式差异（`nodes-base.*` vs `n8n-nodes-base.*`）；验证 profile 选择；IF 节点 branch 参数；自动净化系统 | 工具存在自动参数净化行为——部分格式错误会被自动修正，理解此行为可避免误判和重复重试 |
| **`n8n-workflow-patterns`** | 5 大架构模式（Webhook / HTTP API / 数据库 / AI Agent / 定时任务），每个模式含真实案例（来自 2,653+ 模板） | 先选模式再设计连接；不得跳过模式选择直接堆砌节点 |
| **`n8n-node-configuration`** | 操作感知配置（不同 Operation 需要不同必填字段）；属性依赖规则；AI Agent 8 种连接类型 | 先选 Operation 再填参数；开启自动清理避免脏数据；不同 resource/operation 组合的配置不可移植 |
| **`n8n-expression-syntax`** | `{{}}` 表达式语法；`$json`、`$node`、`$now`、`$env` 变量；常见错误修复 | ⚠️ **Webhook 数据在 `$json.body`**，非顶层 `$json`；⚠️ **Code 节点中禁用表达式**（用 JavaScript/Python 直接处理数据） |
| **`n8n-code-javascript`** | Code 节点 JavaScript 开发；`$input.all()` / `$input.first()` / `$input.item` 数据访问；`$helpers.httpRequest()`、DateTime、`$jmespath()` | ⚠️ **Webhook body 陷阱**：通过 `$json.body` 访问；⚠️ **返回格式**：必须 `[{json: {...}}]`；⚠️ **Top 5 错误模式覆盖 62% 以上失败** |
| **`n8n-code-python`** | Python Code 节点开发；数据访问 `_input` / `_json` / `_node` | ⚠️ **致命限制：无任何第三方库**（无 requests/pandas/numpy），仅标准库；⚠️ **95% 场景推荐用 JavaScript 替代**；网络请求必须用 JS 节点 |
| **`n8n-code-tool`** | AI Agent 的 Custom Code Tool（`@n8n/n8n-nodes-langchain.toolCode`）开发；`specifyInputSchema` 生成 DynamicStructuredTool | ⚠️ **Code Tool ≠ Code 节点**，是完全不同的节点类型；⚠️ **返回格式：必须返回字符串**（`JSON.stringify()`），而非 `[{json:{...}}]`；⚠️ **沙箱限制**：无 `$input`/`$helpers`/`$json`/`$fromAI()`，状态不跨调用保持 |
| **`n8n-validation-expert`** | 验证循环（诊断→修复→再验证）；真实错误目录；自动净化导致的假阳性处理 | 收到验证错误先查错误目录，不要立即修改；自动净化引起的假阳性无需手动修正；开发初期用 `ai-friendly` profile |

### 三、工具协作流程（标准构建循环）

```
1. n8n-mcp-tools-expert       → 确定工具选择策略
2. n8n-workflow-patterns       → 选择架构模式
3. search_nodes                → 发现所需节点
4. get_node (mode: 'info')     → 了解节点配置与必填字段
5. n8n-node-configuration      → 配置节点参数
6. validate_node (mode: 'full') → 验证节点配置
7. n8n_create_workflow         → 创建工作流
8. n8n_validate_workflow       → 验证工作流结构
9. n8n_update_partial_workflow → 增量迭代修改
10. n8n-validation-expert      → 解读并修复验证错误
```

复杂工作流示例（Webhook → Slack）技能自动组合顺序：patterns → tools-expert → node-config → code-javascript → expression-syntax → validation-expert

### 四、nodeType 格式区分（关键）

两类工具使用不同的 nodeType 格式，**不可混用**：

| 工具类别 | 格式 | 示例 |
|----------|------|------|
| 搜索/验证工具（`search_nodes`、`get_node`、`validate_node` 等） | 短前缀 | `nodes-base.slack` |
| 工作流管理工具（`n8n_create_workflow`、`n8n_update_partial_workflow` 等） | 全前缀 | `n8n-nodes-base.slack` |

`search_nodes` 返回结果中可能同时包含两种格式，需根据后续使用的工具类别选择正确格式。

---

## 工作流构建规范

### 质量标准

- 所有节点配置必须通过 `validate_node`（mode: `full`，profile: `runtime`）验证
- 工作流创建后必须通过 `n8n_validate_workflow` 验证
- 错误处理节点必须覆盖所有可能失败的路径
- 节点命名清晰、无歧义，能直观反映职责
- Webhook 类工作流必须处理 `$json.body` 数据结构
- 交付前执行 `n8n_test_workflow` 验证实际运行效果

### 节点设计五原则

1. **渐进式发现**：`get_node` mode:info（detail: minimal → standard → full）→ 必要时 mode:search_properties → 按需 mode:docs，避免一次性加载大量文档
2. **操作感知**：不同 resource/operation 组合需要不同必填字段，不要假设同类节点的配置可互相移植
3. **依赖感知**：使用 `get_property_dependencies`（含于 `get_node`）理解字段可见性与联动规则
4. **善用智能参数**：IF 节点用 `branch: "true"/"false"`，Switch 节点用 `case: 0/1`
5. **最小化配置**：只配置必填字段，渐进式添加可选字段，避免过度配置引入风险

### 错误处理机制

- 使用 **Error Trigger** 节点捕获工作流级别的错误
- 关键节点设置 `continueOnFail: true`，防止单点失败中断整个流程
- HTTP 请求节点配置重试机制（maxTries、retryDelay）
- 数据库操作使用事务保护
- IF / Switch 节点必须处理异常分支，不可遗漏 default/else 路径

### 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| 工作流名称 | `[触发类型] 功能描述` | `[Webhook] Slack 消息通知`、`[Schedule] 每日数据同步` |
| 节点名称 | 中文描述性名称，反映节点职责 | `查询用户数据`、`发送通知`、`格式转换` |
| 节点 ID | 英文 kebab-case 标识符 | `webhook-trigger`、`slack-notify`、`data-transform` |
| Webhook 路径 | kebab-case | `form-submit`、`github-webhook`、`order-callback` |

---

## AI 协作准则

### 核心原则：工具优先，实操为主

1. **所有 n8n 操作必须通过 MCP 工具执行**，禁止输出脱离工具的"示例 JSON"或纯理论方案
2. **先搜后建**：构建前必须使用 `search_nodes` 和 `search_templates` 确认可用节点与已有模板，复用 2,352 个现成模板而非从零开始
3. **先验后改**：节点配置必须在通过 `validate_node` 验证后才能提交到工作流实例
4. **增量迭代**：优先使用 `n8n_update_partial_workflow` 进行增量修改，而非一次性构建完整工作流
5. **激活提醒**：工作流交付后提醒用户在 n8n UI 中手动激活（API 不支持激活操作）
6. **模板复用**：构建前按 `keyword` / `by_nodes` / `by_task` / `by_metadata` 四种模式精准定位可复用模板

### 验证 Profile 选择策略

| Profile | 适用场景 |
|---------|----------|
| `minimal` | 快速检查必填字段（宽松，适合早期探索） |
| `runtime` | 值与类型验证（⭐推荐预部署使用） |
| `ai-friendly` | 减少 AI 辅助配置的误报（开发初期首选） |
| `strict` | 生产环境最大验证（最终交付前） |

### 五大核心工作流模式

1. **Webhook 处理**：接收请求 → 校验（body 解析） → 转换 → 响应/通知
2. **HTTP API 集成**：触发 → HTTP 请求 → 数据转换 → 后续操作 → 错误处理
3. **数据库操作**：调度 → 查询 → 转换 → 写入 → 结果验证
4. **AI Agent 工作流**：触发 → AI Agent（模型 + 工具 + 记忆，8 种连接类型） → 格式化输出
5. **定时任务**：调度 → 获取数据 → 处理 → 交付 → 日志记录

### Code 节点关键契约速查

| 节点类型 | 返回格式 | 数据访问 | 禁区 |
|----------|---------|---------|------|
| Code 节点 (JavaScript) | `[{json: {...}}]` | `$input`、`$json`、`$helpers` | 禁用 `{{}}` 表达式 |
| Code 节点 (Python) | `[{json: {...}}]` | `_input`、`_json`、`_node` | 无第三方库 |
| Code Tool (AI Agent) | **字符串** | `query` / `_query` | 无 `$input`/`$helpers`/`$fromAI`/状态保持 |

### 安全准则

> ⚠️ **绝对不要直接用 AI 编辑生产工作流！** 务必先复制工作流，在开发环境中测试，导出备份，验证无误后再部署到生产环境。

- 凭证通过 `n8n_manage_credentials` 加密管理，绝不硬编码到工作流 JSON 中
- 操作生产实例前使用 `n8n_get_workflow`（mode: minimal）确认工作范围，避免误改活跃工作流
- 使用 `n8n_test_workflow` 验证后再激活
- 通过 `n8n_workflow_versions` 追踪每次变更，支持一键回滚
- 定期使用 `n8n_audit_instance` 进行安全检查

---

## 环境依赖

- **n8n 实例地址** 和 **API Key** 配置于环境变量 `N8N_API_URL` 与 `N8N_API_KEY`
- MCP 服务端连接状态通过 `n8n_health_check` 验证
- MCP 服务端部署选项：Dashboard 托管（dashboard.n8n-mcp.com，免费层每日 100 次调用）、npx 直跑、Docker、Railway 一键部署、本地编译（`npm install && npm run build`）
- 传输模式：stdio（本地）、SSE、streamable HTTP（远程）
- Skill 安装：`/plugin install czlonkowski/n8n-skills`（安装后语义匹配自动激活）
