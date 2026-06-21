# N8N-Demo03 - AI 驱动的 n8n 工作流构建项目

## 📖 项目简介

N8N-Demo03 是一个基于 **AI 驱动的工作流自动化项目**，旨在通过 MCP (Model Context Protocol) 工具和 n8n Skills 实现高质量工作流的智能构建。项目采用"AI 是构建者，而非顾问"的核心理念，通过迭代式开发流程，直接操作 n8n 实例创建工作流。

### 🎯 核心目标

- **直接操作优先**：AI 通过 MCP 工具与 n8n 实例交互，避免仅输出理论方案
- **迭代式构建**：遵循 `搜索 → 获取节点 → 配置 → 验证 → 创建 → 验证` 的循环流程
- **质量内建**：每个工作流交付前必须通过节点级和工作流级双重验证
- **可维护性**：工作流结构清晰、命名规范、错误处理完备

---

## ✨ 功能特性

### 1. **完整的工具体系**
   - **n8n MCP 服务**：支持 1,851 个节点（822 核心 + 1,029 社区）
   - **模板库**：2,352 个可复用模板（AI 元数据覆盖 99.96%）
   - **工作流管理**：CRUD、验证、测试、版本管理、审计等 13 个 API 工具

### 2. **智能构建流程**
   - 自动节点搜索与配置
   - 多维度验证（节点级 + 工作流级）
   - 增量迭代修改
   - 自动错误修复

### 3. **五大核心工作流模式**
   - Webhook 处理流程
   - HTTP API 集成流程
   - 数据库操作流程
   - AI Agent 工作流
   - 定时任务流程

### 4. **完善的错误处理**
   - Error Trigger 节点捕获
   - 重试机制
   - 事务保护
   - 异常分支处理

---

## 📂 项目结构

```
N8N-Demo03/
├── AI_ROLE_PROMPT.md      # AI 角色提示词定义
├── AIGC_Files/            # AIGC 相关文件（243 JSON + 23 MD + 2 PY）
├── CLAUDE.md              # Claude 项目配置
├── CODEBUDDY.md           # CodeBuddy 项目指导文档
├── docker-compose.yml     # Docker 编排配置
├── docs/                  # 项目文档
├── scripts/               # 自动化脚本（8 PY + 3 SH）
│   ├── *.py              # Python 处理脚本
│   └── *.sh              # Shell 部署脚本
├── Workflow/              # n8n 工作流定义（40 JSON + 1 MD）
└── README.md              # 项目说明文档
```

---

## 🚀 快速开始

### 前置条件

1. **n8n 实例**：本地或远程运行的 n8n 实例（默认：`localhost:7890`）
2. **API 凭证**：配置 `N8N_API_URL` 和 `N8N_API_KEY` 环境变量
3. **MCP 服务**：安装 n8n MCP 服务（[安装指南](https://github.com/czlonkowski/n8n-mcp)）
4. **n8n Skills**：安装 n8n-skills 插件（`/plugin install czlonkowski/n8n-skills`）

### 环境配置

```bash
# 设置环境变量
export N8N_API_URL="http://localhost:7890"
export N8N_API_KEY="your_api_key_here"

# 验证连接
n8n_health_check
```

### 安装依赖

```bash
# 安装 n8n MCP 服务（可选方案）
# 方案1：Dashboard 托管（免费层每日 100 次调用）
# 访问 dashboard.n8n-mcp.com

# 方案2：npx 直跑
npx -y @czlonkowski/n8n-mcp

# 方案3：Docker 部署
docker run -p 3456:3456 czlonkowski/n8n-mcp

# 方案4：本地编译
git clone https://github.com/czlonkowski/n8n-mcp.git
cd n8n-mcp
npm install
npm run build
```

---

## 📚 使用指南

### 1. 创建工作流

使用 AI 助手通过 MCP 工具创建工作流：

```
用户：创建一个 [Webhook] Slack 消息通知工作流
AI：将自动执行以下步骤：
  1. 搜索 Slack 和 Webhook 节点
  2. 获取节点配置信息
  3. 验证节点配置
  4. 创建工作流
  5. 验证工作流结构
  6. 测试工作流
```

### 2. 验证工作流

```bash
# 节点级验证
validate_node --nodeType "n8n-nodes-base.slack" --nodeConfig {...}

# 工作流级验证
n8n_validate_workflow --workflowId "abc123"
```

### 3. 更新工作流

```bash
# 增量更新（推荐）
n8n_update_partial_workflow --workflow_id "abc123" --update_operations {...}

# 完整替换
n8n_update_full_workflow --workflow_id "abc123" --new_workflow {...}
```

### 4. 测试工作流

```bash
# 测试工作流
n8n_test_workflow --workflowId "abc123"

# 查看执行历史
n8n_executions --action "list" --workflowId "abc123"
```

---

## 🎨 工作流示例

### 示例 1：Webhook 触发 Slack 通知

**功能**：接收 Webhook 请求，处理后发送 Slack 消息

**节点组成**：
1. Webhook Trigger（接收请求）
2. Code Node（数据转换）
3. Slack Node（发送通知）
4. Respond to Webhook（返回响应）

**使用模板**：
```bash
# 搜索模板
search_templates --mode "keyword" --query "webhook slack"

# 部署模板
n8n_deploy_template --templateId "12345"
```

### 示例 2：定时数据同步

**功能**：每天定时从数据库同步数据到 Google Sheets

**节点组成**：
1. Schedule Trigger（定时触发）
2. MySQL Node（查询数据）
3. Google Sheets Node（写入数据）
4. Email Node（发送执行报告）

### 示例 3：AI Agent 智能客服

**功能**：通过 AI Agent 处理客户咨询

**节点组成**：
1. Chat Trigger（聊天触发）
2. AI Agent Node（AI 处理）
3. Tool Code Node（自定义工具）
4. Memory Node（对话记忆）
5. Respond to Chat（返回回复）

---

## 🛠️ 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| **n8n** | v2.57.3+ | 工作流自动化平台 |
| **MCP (Model Context Protocol)** | - | AI 与 n8n 交互协议 |
| **n8n-skills** | latest | 工作流构建技能包 |
| **Docker** | 20.10+ | 容器化部署 |
| **Python** | 3.8+ | 数据处理脚本 |
| **Node.js** | 18+ | MCP 服务运行环境 |

---

## 📋 开发规范

### 命名规范

| 类别 | 规范 | 示例 |
|------|------|------|
| 工作流名称 | `[触发类型] 功能描述` | `[Webhook] Slack 消息通知` |
| 节点名称 | 中文描述性名称 | `查询用户数据`、`发送通知` |
| 节点 ID | 英文 kebab-case | `webhook-trigger`、`slack-notify` |
| Webhook 路径 | kebab-case | `form-submit`、`github-webhook` |

### 代码规范

1. **渐进式配置**：只配置必填字段，逐步添加可选字段
2. **操作感知**：不同 Operation 需要不同必填字段
3. **错误处理**：关键节点设置 `continueOnFail: true`
4. **凭证管理**：通过 `n8n_manage_credentials` 加密管理

### 验证规范

| 阶段 | 工具 | Profile | 说明 |
|------|------|---------|------|
| 节点配置 | `validate_node` | `ai-friendly` | 开发初期验证 |
| 预部署 | `validate_node` | `runtime` | 值与类型验证 |
| 最终交付 | `validate_node` | `strict` | 生产环境最大验证 |
| 工作流创建 | `n8n_validate_workflow` | - | 工作流结构验证 |

---

## 🔧 常见问题

### Q1：n8n 实例连接失败怎么办？

**A**：检查以下几点：
1. 确认 n8n 实例正在运行（`localhost:7890`）
2. 验证环境变量 `N8N_API_URL` 和 `N8N_API_KEY` 是否正确
3. 运行 `n8n_health_check` 检查连接状态

### Q2：节点验证失败如何排查？

**A**：按照以下步骤：
1. 使用 `get_node` 获取节点完整配置
2. 检查必填字段是否齐全
3. 确认 `nodeType` 格式正确（搜索工具用短前缀，工作流工具用全前缀）
4. 查看 `validate_node` 返回的错误详情

### Q3：如何复用现有模板？

**A**：使用模板工具：
```bash
# 按关键词搜索
search_templates --mode "keyword" --query "slack notification"

# 按节点类型搜索
search_templates --mode "by_nodes" --nodes "['slack', 'webhook']"

# 按任务类型搜索
search_templates --mode "by_task" --task "webhook_processing"
```

### Q4：Code 节点返回格式错误？

**A**：注意 Code 节点的返回格式要求：
- **JavaScript Code 节点**：必须返回 `[{json: {...}}]`
- **Python Code 节点**：必须返回 `[{json: {...}}]`，且无法使用第三方库
- **Code Tool (AI Agent)**：必须返回**字符串**（`JSON.stringify()`）

---

## 📖 参考资料

- **n8n 官方文档**：https://docs.n8n.io/
- **n8n MCP 服务**：https://github.com/czlonkowski/n8n-mcp
- **n8n Skills**：https://github.com/czlonkowski/n8n-skills
- **n8n 模板库**：https://n8n.io/workflows
- **MCP 协议规范**：https://modelcontextprotocol.io/

---

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 提交 Pull Request

### 贡献规范

- 遵循现有代码风格
- 添加必要的测试用例
- 更新相关文档
- 提交前进行代码自查

---

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

## 🙏 致谢

- **n8n 团队**：提供出色的工作流自动化平台
- **MCP 社区**：推动 AI 与应用的交互标准化
- **所有贡献者**：让这个项目变得更好

---

## 📧 联系方式

如有问题或建议，请通过以下方式联系：

- **Issues**：[GitHub Issues](https://github.com/your-repo/N8N-Demo03/issues)
- **Discussions**：[GitHub Discussions](https://github.com/your-repo/N8N-Demo03/discussions)
- **Email**：your-email@example.com

---

**⭐ 如果这个项目对你有帮助，请给它一个星标！**