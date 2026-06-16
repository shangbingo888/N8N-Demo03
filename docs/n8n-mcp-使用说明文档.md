# n8n-mcp 详细使用说明文档

> **版本**: v2.57.3 | **仓库**: [czlonkowski/n8n-mcp](https://github.com/czlonkowski/n8n-mcp)
> **最后更新**: 2026-06-14 | **基于 commit**: b0f5e25d

---

## 目录

- [1. 核心概念与架构原理解析](#1-核心概念与架构原理解析)
  - [1.1 什么是 n8n-mcp](#11-什么是-n8n-mcp)
  - [1.2 系统架构](#12-系统架构)
  - [1.3 核心组件详解](#13-核心组件详解)
  - [1.4 工具体系全景](#14-工具体系全景)
- [2. 环境准备与完整安装配置步骤](#2-环境准备与完整安装配置步骤)
  - [2.1 前置要求](#21-前置要求)
  - [2.2 五种部署方式](#22-五种部署方式)
  - [2.3 Claude Desktop 集成](#23-claude-desktop-集成)
  - [2.4 环境变量详解](#24-环境变量详解)
- [3. 基础功能操作与使用流程](#3-基础功能操作与使用流程)
  - [3.1 核心工具（无需 n8n API）](#31-核心工具无需-n8n-api)
  - [3.2 管理工具（需要 n8n API）](#32-管理工具需要-n8n-api)
  - [3.3 模板系统](#33-模板系统)
  - [3.4 标准构建循环](#34-标准构建循环)
- [4. 最佳实践](#4-最佳实践)
  - [4.1 性能优化](#41-性能优化)
  - [4.2 错误处理](#42-错误处理)
  - [4.3 安全配置](#43-安全配置)
  - [4.4 工作流设计规范](#44-工作流设计规范)
- [5. 常见问题排查与解决方法](#5-常见问题排查与解决方法)

---

## 1. 核心概念与架构原理解析

### 1.1 什么是 n8n-mcp

**n8n-mcp** 是一个 **Model Context Protocol (MCP) 服务器**，作为 AI 助手与 n8n 工作流自动化平台之间的桥梁。它使 AI 能够：

- 🔍 **搜索节点文档**：覆盖 1,236 个节点（812 核心 + 424 社区）
- ✅ **验证工作流配置**：多层验证框架，支持 4 种验证配置文件和 3 种验证模式
- 🔧 **管理实时 n8n 实例**：工作流 CRUD、执行管理、安全审计
- 📋 **复用模板**：2,709 个预建工作流模板，AI 元数据覆盖率 99.96%
- 🛠️ **自动修复**：13 种自动修复类型，置信度评分驱动

#### 核心数据指标

| 指标 | 数值 |
|------|------|
| 节点总数（核心 + 社区） | 1,236 |
| 已验证社区节点 | 911 |
| 工作流模板 | 2,709 |
| AI 工具变体 | 265 |
| 文档工具 | 7（核心），总计 23 |
| 管理工具 | 13（需 n8n API） |
| 真实配置示例 | 156 |

---

### 1.2 系统架构

n8n-mcp 采用 **构建时 + 运行时** 分离的双阶段架构：

```
┌─────────────────────────────────────────────────────────┐
│                    构建时 (Build-Time)                    │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐  │
│  │ Node Loader │ → │  Node Parser │ → │  SQLite DB   │  │
│  │  (节点加载)   │   │  (节点解析)    │   │  (nodes.db)  │  │
│  └─────────────┘   └──────────────┘   └──────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│                    运行时 (Runtime)                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │              MCP Server (核心)                     │   │
│  │  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │   │
│  │  │ 文档工具  │  │ 管理工具  │  │  验证框架     │  │   │
│  │  │  (23个)  │  │  (13个)  │  │  (多层验证)   │  │   │
│  │  └──────────┘  └──────────┘  └───────────────┘  │   │
│  └──────────────────────────────────────────────────┘   │
│         ↓                          ↓                     │
│  ┌───────────┐            ┌──────────────┐              │
│  │   stdio   │            │     HTTP     │              │
│  │  (同步)   │            │ (会话管理)    │              │
│  └───────────┘            └──────────────┘              │
└─────────────────────────────────────────────────────────┘
```

#### 设计特点

| 特性 | 说明 |
|------|------|
| **双传输层** | stdio（本地 AI 助手）+ HTTP/SSE（远程访问、多用户） |
| **模块化架构** | 数据库适配、节点仓库、验证框架、模板管理独立子系统 |
| **适配器模式** | better-sqlite3（原生性能）+ sql.js（WASM 回退） |
| **多租户支持** | `InstanceContext` 实现租户隔离，会话级凭证保护 |
| **渐进式信息加载** | minimal → standard → full 三级详情粒度 |

---

### 1.3 核心组件详解

#### 1.3.1 MCP 服务器核心 (`N8NDocumentationMCPServer`)

| 功能 | 说明 |
|------|------|
| 协议协商 | 确保客户端兼容性 |
| 工具注册 | 注册全部 36 个 MCP 工具 |
| 数据库初始化 | 共享连接池，防止内存泄漏 |
| 请求路由 | MCP 协议请求分发到对应处理器 |
| 多租户上下文 | 支持 `InstanceContext` 注入 |
| 早期错误日志 | 捕获初始化/运行时异常 |
| 扩展工具 | 支持注入宿主特定工具（工具名冲突检测） |

#### 1.3.2 数据库系统 (`nodes.db`)

使用 **SQLite + FTS5 全文搜索引擎**，通过适配器模式支持两种后端：

| 适配器 | 技术 | 特点 | 推荐场景 |
|--------|------|------|----------|
| `BetterSQLite3Adapter` | `better-sqlite3` native 绑定 | 快速、低内存、稳定 | 生产环境（推荐） |
| `SQLJSAdapter` | `sql.js` WebAssembly | 纯 JS，无需编译 | 受限环境、回退方案 |

`SharedDatabaseState` 单例模式确保热重载时不会重复创建连接，防止内存泄漏。

#### 1.3.3 验证框架（多层验证）

系统提供三层独立验证，支持工作流完整性检查：

| 验证器 | 功能 |
|--------|------|
| **WorkflowValidator** | 检查工作流结构和连接完整性 |
| **EnhancedConfigValidator** | 操作感知的参数验证，支持 4 种配置文件 |
| **ExpressionValidator** | 验证 n8n 表达式语法与变量引用正确性 |

**验证模式**控制验证属性范围：

| 模式 | 策略 | 用例 |
|------|------|------|
| `full` | 验证所有属性 | 部署前全面检查 |
| `operation` | 仅验证当前 resource/operation 相关属性 | 渐进式配置 |
| `minimal` | 仅验证可见必填字段 | AI 逐步构建 |

**验证配置文件**控制输出信噪比：

| 配置文件 | 行为 | 适用阶段 |
|----------|------|----------|
| `minimal` | 仅保留缺失必填字段错误 | 早期探索 |
| `runtime` | 仅保留导致运行时失败的严重错误 | 预部署验证 |
| `ai-friendly` ⭐默认 | 保留帮助性警告，过滤内部噪音 | AI 辅助开发 |
| `strict` | 返回全部信息 + 最佳实践建议 | 生产部署前 |

---

### 1.4 工具体系全景

#### 4.1 文档工具（7 个核心，独立运行）

无需 n8n API 密钥即可使用：

| 工具 | 功能 | 关键参数 |
|------|------|----------|
| `search_nodes` | FTS5 全文搜索节点 | `source: 'verified'` 筛选、`includeExamples: true` 获取示例 |
| `get_node` | 统一多模式节点查询 | `mode: 'info'/'docs'/'search_properties'/'versions'/'compare'/'breaking'/'migrations'` |
| `validate_node` | 节点配置验证 | `mode: 'minimal'/'full'`，`profile: minimal/runtime/ai-friendly/strict` |
| `validate_workflow` | 完整工作流验证 | 含连接、表达式、AI Agent 校验 |
| `validate_workflow_connections` | 工作流连接结构检查 | 验证节点间连接正确性 |
| `validate_workflow_expressions` | n8n 表达式校验 | 模板表达式有效性检查 |
| `tools_documentation` | 获取 MCP 工具文档 | `depth: 'essentials'/'full'` |

#### 4.2 模板工具（2 个，独立运行）

| 工具 | 功能 |
|------|------|
| `search_templates` | 四种模式搜索 2,709 个模板：`keyword` / `by_nodes` / `by_task` / `by_metadata` |
| `get_template` | 获取模板详情：`nodes_only` / `structure` / `full` |

#### 4.3 管理工具（13 个，需 n8n API）

配置 `N8N_API_URL` + `N8N_API_KEY` 后解锁：

| 类别 | 工具 | 功能 |
|------|------|------|
| **CRUD** | `n8n_create_workflow` | 创建带节点和连接的新工作流 |
| | `n8n_get_workflow` | 获取工作流（full/details/structure/minimal） |
| | `n8n_update_partial_workflow` | ⭐增量修改（最常用），支持 add/remove/update |
| | `n8n_update_full_workflow` | 完整替换工作流 |
| | `n8n_delete_workflow` | 永久删除工作流 |
| | `n8n_list_workflows` | 列出工作流（支持过滤分页） |
| **验证修复** | `n8n_validate_workflow` | 按 ID 在实例中校验工作流 |
| | `n8n_autofix_workflow` | 自动修复 13 种常见配置错误 |
| | `n8n_test_workflow` | 测试/触发工作流 |
| **运行审计** | `n8n_executions` | 执行管理：list/get/delete |
| | `n8n_manage_credentials` | 凭证管理 CRUD + getSchema |
| | `n8n_audit_instance` | 安全审计（硬编码密钥检测、未认证 Webhook 检测） |
| | `n8n_health_check` | API 连接状态检查 |

---

## 2. 环境准备与完整安装配置步骤

### 2.1 前置要求

| 部署方式 | 依赖 | 适用场景 |
|----------|------|----------|
| **npx**（推荐快速测试） | Node.js 18+ | 本地快速启动，始终使用最新版本 |
| **Docker** | Docker 已安装 | 隔离可复现的生产部署 |
| **本地开发** | Node.js 18+, Git | 修改源代码、调试 |
| **Railway** | Railway 账户 | 零维护云端托管 |
| **HTTP 服务器** | Node.js 18+, 反向代理 | 自定义基础设施、全控 |

---

### 2.2 五种部署方式

#### 方式一：npx（最快，< 1 分钟）

无需永久安装，按需下载并运行：

```bash
# 自动下载 n8n-mcp 包并启动 stdio 模式
npx -y n8n-mcp
```

内部流程：
1. 从 npm 下载 `n8n-mcp` 包
2. 启动 `N8NDocumentationMCPServer`（stdio 模式，stdin/stdout JSON-RPC）
3. 使用预建 SQLite 数据库 `data/nodes.db` 提供节点数据
4. 默认暴露核心文档工具

#### 方式二：Docker（生产就绪，2-5 分钟）

```bash
# 拉取多架构镜像（amd64/arm64）
docker pull ghcr.io/czlonkowski/n8n-mcp:latest

# 启动 stdio 模式（用于 Claude Desktop）
docker run -i --init \
  -e MCP_MODE=stdio \
  -e LOG_LEVEL=error \
  -e DISABLE_CONSOLE_OUTPUT=true \
  ghcr.io/czlonkowski/n8n-mcp:latest

# 启动 HTTP 模式（远程访问）
docker run -d -p 3000:3000 \
  -e MCP_MODE=http \
  -e AUTH_TOKEN=your-secure-token-at-least-32-chars \
  -e N8N_API_URL=https://your-n8n-instance.com \
  -e N8N_API_KEY=your-api-key \
  ghcr.io/czlonkowski/n8n-mcp:latest
```

**镜像标签**：
- `ghcr.io/czlonkowski/n8n-mcp`：通用多架构镜像
- `ghcr.io/czlonkowski/n8n-mcp-railway`：Railway 优化版（仅 amd64）

**关键参数**：
- `-i`：保持交互模式供 stdio 使用
- `--init`：启用信号处理，保证优雅退出
- 镜像大小约 280 MB，零 n8n 运行时依赖

#### 方式三：本地开发（5-10 分钟）

```bash
# 1. 克隆仓库
git clone https://github.com/czlonkowski/n8n-mcp.git
cd n8n-mcp

# 2. 安装依赖
npm install

# 3. 重建节点数据库
npm run rebuild

# 4. 编译 TypeScript
npm run build

# 5. 启动服务
npm start
```

**注意**：Claude Desktop 配置中必须使用编译后入口点的**绝对路径**。

#### 方式四：Railway 云部署（3-5 分钟）

1. Fork 仓库到自己的 GitHub 账户
2. 在 Railway 中连接仓库
3. 设置环境变量（`MCP_MODE=http`、`AUTH_TOKEN` 等）
4. Railway 自动构建并部署，自动配置 HTTPS

#### 方式五：HTTP 服务器部署（10-15 分钟）

```bash
# 1. 安装 Node.js 18+
# 2. 克隆并构建项目（同本地开发步骤）

# 3. 配置环境变量
export MCP_MODE=http
export AUTH_TOKEN=your-secure-token-at-least-32-chars
export PORT=3000
export TRUST_PROXY=1  # 在反向代理后运行时

# 4. 配置反向代理（nginx 示例）
# location /mcp {
#     proxy_pass http://127.0.0.1:3000;
#     proxy_http_version 1.1;
#     proxy_set_header Upgrade $http_upgrade;
#     proxy_set_header Connection "upgrade";
#     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
# }

# 5. 启动
npm start
```

---

### 2.3 Claude Desktop 集成

#### 配置文件位置

| 操作系统 | 配置路径 |
|----------|----------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/Claude/claude_desktop_config.json` |

#### npx 方式配置

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "npx",
      "args": ["-y", "n8n-mcp"],
      "env": {
        "N8N_API_URL": "http://localhost:5678",
        "N8N_API_KEY": "Bearer your-jwt-token",
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true"
      }
    }
  }
}
```

#### Docker 方式配置

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm", "--init",
        "-e", "MCP_MODE=stdio",
        "-e", "LOG_LEVEL=error",
        "-e", "DISABLE_CONSOLE_OUTPUT=true",
        "-e", "N8N_API_URL=https://your-n8n.com",
        "-e", "N8N_API_KEY=Bearer your-token",
        "ghcr.io/czlonkowski/n8n-mcp:latest"
      ]
    }
  }
}
```

#### 本地开发方式配置

```json
{
  "mcpServers": {
    "n8n-mcp": {
      "command": "node",
      "args": ["/absolute/path/to/n8n-mcp/dist/mcp/index.js"],
      "env": {
        "LOG_LEVEL": "error",
        "DISABLE_CONSOLE_OUTPUT": "true"
      }
    }
  }
}
```

#### 验证安装

1. 重启 Claude Desktop
2. 检查 MCP 服务器列表（插头图标）中 `n8n-mcp` 是否出现
3. 在对话中询问：*"列出 n8n-mcp 提供的所有工具"*
4. 预期工具列表包含 `search_nodes`、`get_node`、`search_templates` 等

---

### 2.4 环境变量详解

#### 运行模式

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `MCP_MODE` | 否（默认 stdio） | `stdio` | `stdio`（本地）或 `http`（远程） |
| `LOG_LEVEL` | 否 | `info` | 日志级别，Claude 集成建议 `error` |
| `DISABLE_CONSOLE_OUTPUT` | 否（强烈建议） | `false` | 禁用控制台输出，防止破坏 stdio 流 |
| `IS_DOCKER` | 否 | - | Docker 环境下影响信号处理 |

#### HTTP 模式认证（`MCP_MODE=http` 时必填）

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `MCP_MODE` | 是 | - | 必须设为 `http` |
| `AUTH_TOKEN` | 二选一 | - | Bearer 认证令牌（≥32 字符） |
| `AUTH_TOKEN_FILE` | 二选一 | - | 令牌文件路径（Docker secrets 推荐） |
| `PORT` | 否 | `3000` | HTTP 服务监听端口 |
| `TRUST_PROXY` | 否 | `0` | 信任代理头（反向代理后设为 `1`） |

#### n8n API 集成（启用 13 个管理工具）

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `N8N_API_URL` | 是 | - | n8n 实例的基础 URL |
| `N8N_API_KEY` | 是 | - | n8n API 密钥（JWT Bearer Token） |
| `N8N_API_TIMEOUT` | 否 | `30000` | API 请求超时（毫秒） |

#### 数据库配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `NODE_DB_PATH` | `./data/nodes.db` | SQLite 数据库文件路径 |
| `REBUILD_ON_START` | `false` | 启动时重建数据库 |

#### 安全配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `WEBHOOK_SECURITY_MODE` | `strict` | SSRF 防护：strict / moderate / permissive |
| `AUTH_RATE_LIMIT_WINDOW` | `900000`（15 分钟） | 限流时间窗口（毫秒） |
| `AUTH_RATE_LIMIT_MAX` | `20` | 单 IP 最大认证尝试次数 |
| `N8N_MCP_MAX_SESSIONS` | `100` | HTTP 模式最大会话数 |
| `N8N_MCP_TELEMETRY_DISABLED` | `false` | 禁用遥测 |

#### 多租户配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `ENABLE_MULTI_TENANT` | `false` | 启用动态实例切换 |
| `MULTI_TENANT_SESSION_STRATEGY` | `instance` | 会话策略：`instance`（隔离）或 `shared` |

---

## 3. 基础功能操作与使用流程

### 3.1 核心工具（无需 n8n API）

#### search_nodes — 搜索节点

```javascript
// 基础搜索
search_nodes({ query: "slack" })
search_nodes({ query: "webhook", source: "verified" })

// 带示例的高级搜索（推荐）
search_nodes({
  query: "database postgres",
  mode: "AND",
  includeExamples: true,
  includeOperations: true,
  source: "core"
})
```

#### get_node — 渐进式获取节点信息

```javascript
// 第一步：最小信息（~200 tokens）
get_node({ nodeType: "nodes-base.slack", detail: "minimal" })

// 第二步：标准信息（~1-2K tokens），获取必填字段和属性
get_node({ nodeType: "nodes-base.slack", detail: "standard" })

// 第三步：完整信息（~3-8K tokens），全部属性详情
get_node({ nodeType: "nodes-base.slack", detail: "full" })

// 其他模式
get_node({ nodeType: "nodes-base.slack", mode: "docs" })              // Markdown 文档
get_node({ nodeType: "nodes-base.slack", mode: "search_properties", propertyQuery: "auth" })  // 搜索属性
get_node({ nodeType: "nodes-base.httpRequest", mode: "versions" })     // 版本历史
```

#### validate_node — 节点配置验证

```javascript
// 快速必填字段检查
validate_node({
  nodeType: "nodes-base.slack",
  config: { resource: "channel", operation: "create" },
  mode: "minimal"
})

// AI 友好的全面验证（推荐开发时使用）
validate_node({
  nodeType: "nodes-base.slack",
  config: { resource: "channel", operation: "create" },
  mode: "full",
  profile: "ai-friendly"
})

// 部署前严格验证
validate_node({
  nodeType: "nodes-base.slack",
  config: { /* 完整配置 */ },
  mode: "full",
  profile: "strict"
})
```

---

### 3.2 管理工具（需要 n8n API）

#### 工作流全生命周期

```javascript
// 创建
n8n_create_workflow({
  name: "[Webhook] 表单数据处理",
  nodes: [...],
  connections: {...}
})

// 读取
n8n_get_workflow({ id: "workflow-id", mode: "full" })

// 增量更新（最常用，手术式修改）
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [
    { action: "add", node: {...} },
    { action: "update", nodeId: "node-1", node: {...} },
    { action: "remove", nodeId: "node-2" },
    { action: "add", connection: { from: "a", to: "b" } }
  ]
})

// 自动修复
n8n_autofix_workflow({ id: "workflow-id", mode: "preview" })  // 先预览
n8n_autofix_workflow({ id: "workflow-id", mode: "apply" })    // 再应用

// 测试
n8n_test_workflow({ id: "workflow-id" })

// 安全审计
n8n_audit_instance({ scanDepth: "deep" })
```

---

### 3.3 模板系统

#### search_templates — 四种搜索模式

```javascript
// 按关键词
search_templates({ query: "slack notification", mode: "keyword" })

// 按节点类型（查找使用了特定节点的模板）
search_templates({ nodeTypes: ["nodes-base.slack", "nodes-base.webhook"], mode: "by_nodes" })

// 按任务类型
search_templates({ task: "webhook_processing", mode: "by_task" })

// 按元数据（复杂度、目标用户、所需服务）
search_templates({
  filters: { complexity: "beginner", service: "slack" },
  mode: "by_metadata"
})
```

---

### 3.4 标准构建循环

推荐的 AI 构建工作流标准流程（迭代式）：

```
1. n8n-mcp-tools-expert       → 确定工具选择策略
2. n8n-workflow-patterns       → 选择架构模式（5 大模式）
3. search_nodes                → 发现所需节点
4. get_node (mode: 'info')     → 渐进式了解节点配置
5. n8n-node-configuration      → 配置节点参数（操作感知）
6. validate_node (mode: 'full') → 验证节点配置
7. n8n_create_workflow         → 创建工作流
8. n8n_validate_workflow        → 验证工作流结构
9. n8n_update_partial_workflow  → 增量迭代修改
10. n8n-validation-expert       → 解读并修复验证错误
```

#### 验证配置文件选择策略

| 配置文件 | 适用场景 |
|----------|----------|
| `minimal` | 快速检查必填字段（宽松，适合早期探索） |
| `runtime` | 值与类型验证（⭐推荐预部署使用） |
| `ai-friendly` | 减少 AI 辅助配置的误报（开发初期首选） |
| `strict` | 生产环境最大验证（最终交付前） |

#### 五大核心工作流模式

| 模式 | 结构 | 典型场景 |
|------|------|----------|
| **Webhook 处理** | 接收 → 校验(body) → 转换 → 响应/通知 | GitHub webhook、表单提交 |
| **HTTP API 集成** | 触发 → HTTP 请求 → 数据转换 → 后续操作 → 错误处理 | Slack 通知、第三方 API 调用 |
| **数据库操作** | 调度 → 查询 → 转换 → 写入 → 结果验证 | 数据同步、报表生成 |
| **AI Agent** | 触发 → AI Agent（模型+工具+记忆） → 格式化输出 | 智能客服、自动化分析 |
| **定时任务** | 调度 → 获取数据 → 处理 → 交付 → 日志记录 | 每日报表、定期清理 |

---

## 4. 最佳实践

### 4.1 性能优化

#### 4.1.1 渐进式信息加载

不要一次性请求所有节点信息，而是遵循 "最小 → 标准 → 完整" 的渐进策略：

```javascript
// ✅ 推荐：渐进式
get_node({ nodeType: "nodes-base.slack", detail: "minimal" })      // ~200 tokens
// → 发现需要了解 channel 操作的必填字段
get_node({ nodeType: "nodes-base.slack", detail: "standard" })      // ~1-2K tokens
// → 仅在需要深入时
get_node({ nodeType: "nodes-base.slack", detail: "full" })           // ~3-8K tokens

// ❌ 避免：一次加载全部
get_node({ nodeType: "nodes-base.slack", detail: "full" })           // 浪费 token
```

#### 4.1.2 使用 includeOperations 减少往返

在 `search_nodes` 中启用 `includeOperations: true` 可以一次性获取节点的 resource/operation 树，避免额外的 `get_node` 调用：

```javascript
search_nodes({
  query: "database",
  includeOperations: true, // 一次获取操作信息，节省往返
  source: "core"
})
```

#### 4.1.3 数据库适配器选择

| 环境 | 推荐适配器 | 原因 |
|------|------------|------|
| 生产 Linux/macOS | `better-sqlite3` | 原生性能，低内存，查询速度快 3-5x |
| 受限环境 | `sql.js` | 无需编译，但内存占用高、速度慢 |
| Docker | `better-sqlite3`（默认） | 镜像内置编译支持 |

#### 4.1.4 优先使用增量更新

使用 `n8n_update_partial_workflow` 而非 `n8n_update_full_workflow`：

```javascript
// ✅ 推荐：手术式增量修改
n8n_update_partial_workflow({
  id: "workflow-id",
  operations: [{ action: "update", nodeId: "node-1", node: { name: "新名称" } }]
})

// ❌ 避免：完整替换（除非必要）
n8n_update_full_workflow({ id: "workflow-id", workflow: { /* 整个工作流 */ } })
```

#### 4.1.5 版本检测缓存

系统自动对 n8n 实例版本进行多层缓存（实例级 + 进程级），减少 API 调用开销。无需手动干预。

---

### 4.2 错误处理

#### 4.2.1 自动修复系统（13 种修复类型）

使用 `n8n_autofix_workflow` 自动处理常见问题，**先预览、再应用**：

| 类别 | 修复类型 | 置信度 | 触发条件 |
|------|---------|--------|----------|
| **表达式格式** | `expression-format` | 高 | `{{ $json.id }}` → `={{ $json.id }}` |
| **类型版本** | `typeversion-correction` | 高 | 无效 typeVersion |
| | `typeversion-upgrade` | 中 | 可用的新版本 |
| | `version-migration` | 中 | 属性已弃用 |
| **节点配置** | `error-output-config` | 高 | 缺失错误输出 |
| | `node-type-correction` | 高 | 大小写/前缀错误 |
| | `webhook-missing-path` | 高 | Webhook 无路径 |
| | `tool-variant-correction` | 中 | AI 工具变体不匹配 |
| **连接结构** | `connection-numeric-keys` | 高 | 数字键需改名为字符串 |
| | `connection-invalid-type` | 高 | 无效连接类型 |
| | `connection-id-to-name` | 高 | ID 需转为名称 |
| | `connection-duplicate-removal` | 中 | 重复连接 |
| | `connection-input-index` | 高 | 越界连接索引 |

#### 4.2.2 工作流错误处理策略

```
关键原则：错误处理节点必须覆盖所有可能失败的路径

推荐模式：
┌──────────┐    ┌──────────┐    ┌──────────┐
│  触发节点  │ → │  HTTP 请求 │ → │  处理结果  │
└──────────┘    └─────┬─────┘    └──────────┘
                      │ (失败时)
                      ↓
                ┌──────────┐
                │ Error    │
                │ Trigger  │
                └────┬─────┘
                     ↓
                ┌──────────┐
                │ 错误通知  │  ← Slack/Email
                └──────────┘
```

**关键配置**：
- 使用 **Error Trigger** 节点捕获工作流级别错误
- 关键 HTTP 节点设置 `continueOnFail: true` + 重试机制
- 数据库操作使用事务保护
- IF/Switch 节点必须处理所有分支（含 default/else）

#### 4.2.3 验证错误修复流程

```
验证错误 → 查错误目录 → 确定修复类型 → 自动修复（优先） → 手动修复（如需要） → 再验证
```

利用 `validate_node` 的配置文件控制：
- 开发初期用 `ai-friendly`，过滤噪音
- 部署前用 `strict`，全面检查

---

### 4.3 安全配置

#### 4.3.1 认证机制（HTTP 模式）

**Token 要求**：
- 长度 ≥ **32 字符**
- 不可为空或仅含空白
- 生产环境 **禁止使用** 默认占位 token

```bash
# ✅ 正确：生成安全 token
AUTH_TOKEN=$(openssl rand -hex 32)

# ✅ 使用文件方式（更安全，适合 Docker/K8s secrets）
AUTH_TOKEN_FILE=/run/secrets/mcp-auth-token

# ❌ 错误：短 token
AUTH_TOKEN=short
```

**时序安全比较**：系统使用 `timingSafeCompare()` 防止时序攻击。

#### 4.3.2 SSRF 防护

| 模式 | localhost | 私有 IP | 云元数据（169.254.169.254） |
|------|-----------|---------|----------------------------|
| `strict`（默认推荐） | ❌ 禁止 | ❌ 禁止 | ❌ 始终禁止 |
| `moderate` | ✅ 允许 | ❌ 禁止 | ❌ 始终禁止 |
| `permissive` | ✅ 允许 | ✅ 允许 | ❌ 始终禁止 |

> 云元数据端点在**所有模式**下均被永久阻止。

**DNS 重绑定防御**：
验证前通过 `dns/promises` 解析主机名到 IP 地址，防止攻击者在初始检查后切换 IP。

**IPv6 隧道防御**：
检测并解析 IPv6-to-IPv4 隧道（NAT64、6to4、Teredo），提取内嵌 IPv4 地址并应用相同策略。

#### 4.3.3 速率限制

```bash
# 默认：15 分钟内每 IP 最多 20 次认证尝试
AUTH_RATE_LIMIT_WINDOW=900000
AUTH_RATE_LIMIT_MAX=20

# 生产环境推荐配置
AUTH_RATE_LIMIT_WINDOW=300000   # 5 分钟
AUTH_RATE_LIMIT_MAX=10          # 最多 10 次
```

#### 4.3.4 会话安全

- **超时时间**：默认 5 分钟无活动
- **最大会话数**：`N8N_MCP_MAX_SESSIONS`（默认 100）
- **多租户隔离**：凭证限制在会话内，超时后不持久化
- **安全头自动注入**：
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 1; mode=block`
  - `Strict-Transport-Security`（HTTPS 时）

#### 4.3.5 数据脱敏

系统自动从工具输出和日志中**剥离敏感字段**（credentials、API keys），`N8nApiClient` 将原始 Axios 错误转换为类型化 `N8nApiError`，避免泄露内部堆栈。

#### 4.3.6 安全操作准则

> ⚠️ **绝对不要直接用 AI 编辑生产工作流！**

- 先复制工作流，在开发环境测试
- 导出备份后再部署
- 凭证通过 `n8n_manage_credentials` 加密管理，**绝不硬编码**到工作流 JSON
- 使用 `n8n_audit_instance` 定期扫描：
  - 检测硬编码密钥
  - 检测未认证的公开 Webhook
- 通过 `n8n_workflow_versions` 追踪变更，支持一键回滚

---

### 4.4 工作流设计规范

#### 4.4.1 节点设计五原则

| 原则 | 说明 | 实践方法 |
|------|------|----------|
| **渐进式发现** | 避免一次性加载大量文档 | minimal → standard → full |
| **操作感知** | 不同 resource/operation 需要不同必填字段 | 先选 Operation 再填参数 |
| **依赖感知** | 理解字段可见性与联动规则 | 使用 `get_property_dependencies` |
| **善用智能参数** | IF 用 `branch: "true"/"false"`，Switch 用 `case: 0/1` | 避免技术参数 `sourceIndex` |
| **最小化配置** | 只配置必填字段，渐进式添加可选字段 | 避免过度配置引入风险 |

#### 4.4.2 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| 工作流名称 | `[触发类型] 功能描述` | `[Webhook] Slack 消息通知`、`[Schedule] 每日数据同步` |
| 节点名称 | 中文描述性名称 | `查询用户数据`、`发送通知`、`格式转换` |
| 节点 ID | 英文 kebab-case | `webhook-trigger`、`slack-notify`、`data-transform` |
| Webhook 路径 | kebab-case | `form-submit`、`github-webhook`、`order-callback` |

#### 4.4.3 nodeType 格式区分（关键）

> **两类工具使用不同的 nodeType 格式，不可混用！**

| 工具类别 | 格式 | 示例 |
|----------|------|------|
| 搜索/验证工具 | 短前缀 | `nodes-base.slack` |
| 工作流管理工具 | 全前缀 | `n8n-nodes-base.slack` |

#### 4.4.4 Code 节点关键契约

| 节点类型 | 返回格式 | 数据访问 | 禁区 |
|----------|---------|---------|------|
| Code (JavaScript) | `[{json: {...}}]` | `$input`、`$json`、`$helpers` | 禁用 `{{}}` 表达式 |
| Code (Python) | `[{json: {...}}]` | `_input`、`_json`、`_node` | **无第三方库**（无 requests/pandas） |
| Code Tool (AI Agent) | **字符串** | `query` / `_query` | 无 `$input`/`$helpers`/`$fromAI` |

#### 4.4.5 质量检查清单

交付工作流前逐项确认：

- [ ] 所有节点通过 `validate_node`（profile: `strict`）
- [ ] 工作流通过 `n8n_validate_workflow` 验证
- [ ] 错误处理节点覆盖所有可能失败的路径
- [ ] 关键节点设置了 `continueOnFail: true` 和重试机制
- [ ] IF/Switch 节点处理了所有分支（含 default/else）
- [ ] Webhook 类工作流处理了 `$json.body` 数据结构
- [ ] 节点命名清晰、反映职责
- [ ] 通过 `n8n_test_workflow` 验证实际运行效果
- [ ] 通过 `n8n_audit_instance` 安全检查

---

## 5. 常见问题排查与解决方法

### 5.1 连接与启动问题

| 问题 | 诊断方法 | 解决方案 |
|------|----------|----------|
| **Claude 中不显示 n8n-mcp 服务器** | 检查 JSON 格式、路径 | 用 `jq` 验证 JSON；使用绝对路径；确保 `LOG_LEVEL=error` |
| **JSON-RPC 通信错误** | 控制台日志破坏 stdio 流 | 设置 `DISABLE_CONSOLE_OUTPUT=true`、`LOG_LEVEL=error` |
| **数据库文件缺失** | SQLite 数据库未找到 | 确保 `data/nodes.db` 存在或正确设置 `NODE_DB_PATH` |
| **Node.js 版本不兼容** | 报错 `TransformStream` 等 | 升级至 Node.js 18+ |
| **HTTP 模式无法认证** | Token 长度不足 | Token 必须 ≥ 32 字符 |
| **HTTP 模式无法启动（生产）** | 使用了默认 token | 生产模式下默认 token 会导致拒绝启动 |

### 5.2 工具使用问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| `search_nodes` 返回空结果 | 查询模式不匹配 | 尝试 `mode: "FUZZY"`（容错）或 `mode: "OR"`（宽松） |
| `get_node` 返回信息不完整 | 使用了默认 `minimal` 详情 | 指定 `detail: "standard"` 或 `"full"` |
| 管理工具不可用 | 未配置 n8n API | 设置 `N8N_API_URL` + `N8N_API_KEY` |
| `validate_node` 假阳性错误 | 配置文件过于严格 | 切换为 `profile: "ai-friendly"` |
| nodeType 格式报错 | 工具类型不匹配 | 搜索工具用短前缀 `nodes-base.*`，管理工具用全前缀 `n8n-nodes-base.*` |

### 5.3 工作流验证问题

| 问题 | 诊断 | 解决方案 |
|------|------|----------|
| **"Node expects but got" 错误** | 节点间数据类型不匹配 | 使用 Code 节点或 Item Lists 节点转换数据格式 |
| **表达式解析错误** | `{{}}` 格式不正确 | n8n 表达式需 `={{ }}` 格式；Code 节点禁用表达式 |
| **Webhook 数据为空** | 未正确处理 body | Webhook 数据在 `$json.body`，非顶层 `$json` |
| **字段不可见** | displayOptions 条件未满足 | 先设置 resource/operation 再配置字段；使用 `operation` 验证模式 |
| **连接类型无效** | 节点连接不正确 | 运行 `n8n_autofix_workflow` 自动修复连接问题 |

### 5.4 验证错误修复策略

```
验证错误分类处理：

1. 高置信度（>90%） → n8n_autofix_workflow 自动修复
   - 表达式格式、Webhook 路径、节点类型大小写、连接键格式

2. 中置信度（70-89%） → 预览后决定
   - 版本升级、属性迁移、重复连接

3. 低置信度（<70%） → 手动修复
   - 业务逻辑相关、复杂配置问题
```

### 5.5 Code 节点常见陷阱

| 陷阱 | 错误做法 | 正确做法 |
|------|----------|----------|
| **Webhook body** | `$json.name` | `$json.body.name` |
| **JS 返回格式** | `return data` | `return [{json: data}]` |
| **Python 第三方库** | `import requests` | Python 无第三方库，网络请求用 JS 节点 |
| **Code Tool 返回** | `return [{json: {}}]` | `return JSON.stringify(result)`（必须是字符串） |
| **Code 节点中使用表达式** | `const x = {{ $json.id }}` | `const x = $input.first().json.id` |

### 5.6 健康检查与监控

```bash
# 检查 HTTP 服务健康状态
curl http://localhost:3000/health

# 预期响应
{
  "status": "healthy",
  "version": "2.57.3",
  "mode": "http",
  "database": "better-sqlite3"
}
```

### 5.7 n8n API 连接问题

```javascript
// 快速诊断
n8n_health_check()
// 返回连接状态、API 可用性、版本信息

// 检查凭证
n8n_manage_credentials({ action: "list" })
// 确认凭据配置正确
```

---

## 附录 A：工具兼容性矩阵

| MCP 工具 | 自动修复 | 表达式验证 | 智能参数 | 相似度 | 遥测 | 执行分析 | 版本检测 |
|----------|:--------:|:--------:|:--------:|:------:|:----:|:--------:|:--------:|
| `validate_node` | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| `validate_workflow` | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ❌ |
| `n8n_autofix_workflow` | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| `n8n_update_partial_workflow` | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| `n8n_executions` | ❌ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| `n8n_validate_workflow` | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |

## 附录 B：部署方式功能矩阵

| 功能 | npx | Docker | 本地开发 | Railway | HTTP 服务器 |
|------|-----|--------|----------|---------|-------------|
| stdio 模式 | ✅ | ✅ | ✅ | ❌ | ❌ |
| HTTP 模式 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 多租户支持 | ❌ | ✅ | ✅ | ✅ | ✅ |
| 数据库自定义 | ❌ | 有限 | ✅ | 有限 | ✅ |
| 自动更新 | ✅ | CI/CD | 手动 | ✅ | 手动 |
| 预构建数据库 | ✅ | ✅ | ❌ | ✅ | ❌ |

---

## 附录 C：安全快速参考

| 类别 | 推荐配置 | 说明 |
|------|----------|------|
| **认证 Token** | `openssl rand -hex 32` | 至少 32 字符，文件方式更安全 |
| **SSRF 防护** | `WEBHOOK_SECURITY_MODE=strict` | 阻止 localhost + 私有 IP + 元数据 |
| **速率限制** | 窗口 5 分钟，最多 10 次 | 生产环境收紧默认值 |
| **代理信任** | `TRUST_PROXY=1` | 仅反向代理后启用 |
| **会话管理** | `N8N_MCP_MAX_SESSIONS=100` | 5 分钟无活动超时 |
| **安全头** | 自动注入 | X-Content-Type-Options, X-Frame-Options, XSS, HSTS |

---

> **参考资源**：
> - 仓库：[github.com/czlonkowski/n8n-mcp](https://github.com/czlonkowski/n8n-mcp)
> - DeepWiki：[deepwiki.com/czlonkowski/n8n-mcp](https://deepwiki.com/czlonkowski/n8n-mcp)
> - n8n Skills：[github.com/czlonkowski/n8n-skills](https://github.com/czlonkowski/n8n-skills)
> - MCP 协议：[modelcontextprotocol.io](https://modelcontextprotocol.io)
