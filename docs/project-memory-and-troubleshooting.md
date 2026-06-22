# 项目记忆与问题排查手册

> 最后更新：2026-06-21 | 维护者：Allen Fang
>
> **用途**：本文档是 N8N-Demo03 项目的「大脑」——记录架构全貌、关键决策、历史变更、所有已知陷阱及其解决方案。每次排障后更新，确保知识不丢失。

---

## 第一部分：记忆整理

### 1.1 项目身份

| 属性 | 值 |
|------|-----|
| 项目名称 | N8N-Demo03 |
| 核心定位 | AI 驱动的 n8n 工作流构建——AI 是构建者，非顾问 |
| n8n 实例 | Docker 部署，`localhost:7890` |
| API 版本 | n8n v2.5.0 (Task Runner 沙箱) |
| MCP 服务 | n8n-mcp v2.46.1，stdio 传输模式 |
| 工作流总数 | 26 个（8 个活跃） |

### 1.2 基础设施架构

```
┌──────────────────────────────────────┐
│         docker-compose               │
│                                      │
│  ┌──────────────┐  ┌──────────────┐ │
│  │ n8n-demo03   │  │ n8n-composer │ │
│  │ (n8n 主服务)  │  │ (视频合成服务) │ │
│  │ image: local  │  │ Dockerfile.  │ │
│  │ port: 7890→   │  │ composer     │ │
│  │       5678    │  │ port: 8899   │ │
│  └──────┬───────┘  └──────┬───────┘ │
│         │                 │          │
│         └─── n8n-network ─┘          │
│                                      │
│  Volumes:                            │
│  ├─ n8n-data → /home/node/.n8n      │
│  └─ n8n-files → /files (共享)        │
└──────────────────────────────────────┘

外部依赖：
  ├─ api.xiaomimimo.com  (Mimo TTS)
  ├─ apihub.agnes-ai.com (Agnes AI/Image)
  └─ openai 兼容 API     (通过 OPENAI_BASE_URL)
```

### 1.3 核心服务

| 服务 | 容器名 | 端口 | 基础镜像 | 职责 |
|------|--------|------|----------|------|
| **n8n** | `n8n-demo03` | 7890:5678 | `n8nio/n8n:2.5.0` + ffmpeg | 工作流引擎 |
| **composer** | `n8n-composer` | 8899:8899 | `python:3.11-slim` + ffmpeg | FFmpeg 视频合成 |

### 1.4 关键环境变量

```yaml
# n8n 运行时
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_PROTOCOL=http
NODE_FUNCTION_ALLOW_EXTERNAL=*     # ⚠️ 允许 Code 节点 require 任意模块

# API Keys（来自 .env 文件，docker-compose 必须显式声明）
AGNES_API_KEY=${AGNES_API_KEY}     # Agnes AI / Image API
MIMO_API_KEY=${MIMO_API_KEY}       # Mimo TTS API
OPENAI_API_KEY=${OPENAI_API_KEY}    # OpenAI 兼容 API
OPENAI_BASE_URL=${OPENAI_BASE_URL:-https://apihub.agnes-ai.com/v1}

# 数据管理
EXECUTIONS_DATA_PRUNE_ENABLED=true  # 自动清理执行记录
EXECUTIONS_DATA_MAX_AGE=168         # 保留 7 天
N8N_PAYLOAD_SIZE_MAX=64             # 最大 payload 64MB
```

### 1.5 工作流分类

#### 生产工作流（活跃）

| 工作流 | ID | 节点数 | 触发方式 | Webhook 路径 |
|--------|-----|--------|----------|-------------|
| **[Webhook] 00-文生视频（合并版）** | `S5r7jE8tY3UJa15j` | 18 | Webhook POST | `text-to-video` |
| [Webhook] 01-内容分析与分镜 | `JjMxOUIMgJBpwxer` | 5 | Webhook | - |
| [Webhook] 02-文生图适配层 | `iD87BeQkqIZCLWiM` | 7 | Webhook | - |
| [Webhook] 03-文生音频适配层 | `7aA8FNq2ixjuphuX` | 6 | Webhook | - |
| [Webhook] 04-视频合成 | `MuNuZNCICl5kMqhQ` | 5 | Webhook | - |
| [Manual] 00-主编排-文生视频 | `mmDE4qQKJHqdIZN7` | 8 | 手动 | - |
| [Webhook] Mimo TTS | `iw9ZqJxe-HjcB9Sbsfazk` | 5 | Webhook | - |
| [TEST] Minimal Webhook Echo | `D7BPgaStrmaCb4XW` | 2 | Webhook | - |

#### 文生视频流水线全景

```
用户请求 (Webhook: text-to-video)
  │
  ├─ 1. 校验输入参数 (prompt, duration)
  ├─ 2. 构建AI分镜Prompt
  ├─ 3. 调用AI生成分镜 ──→ 解析分镜输出 (Stream 修复点)
  │       │
  │       ├─ 4a. 构建生图请求 → 调用Agnes生图API → 提取图片URL → 下载图片 → 标准化
  │       │
  │       └─ 4b. 构建TTS请求 → 调用Mimo TTS API → Base64解码 → 标准化
  │
  ├─ 5. 汇总结果
  ├─ 6. 调用合成服务 (composer:8899)
  └─ 7. 检查视频结果 → 返回结果
```

#### 测试/调试工作流

| 工作流 | 用途 |
|--------|------|
| [DEBUG] Raw Mimo API Test | Mimo API 原始响应调试 |
| [DEBUG] Dump Mimo Raw Response | Mimo 响应体导出 |
| [TEST] Webhook Echo Test | Webhook 连通性测试 |
| [TEST] 2-Node Chain | 最小节点链测试 |

### 1.6 关键决策记录

| 日期 | 决策 | 原因 | 影响 |
|------|------|------|------|
| 2026-06-14 | Docker 部署 n8n v2.5.0 | 隔离环境、ffmpeg 集成 | 引入 Task Runner 沙箱限制 |
| 2026-06-14 | 使用 `NODE_FUNCTION_ALLOW_EXTERNAL=*` | Code 节点需要 `Buffer` 等模块 | 安全权衡：允许所有模块 |
| 2026-06-18 | 拆分文生视频为子工作流 | 降低单工作流复杂度 | 引入 `[Manual] 主编排` 协调 |
| 2026-06-20 | 合并为单工作流 `00-文生视频（合并版）` | 减少调试复杂度 | 18 节点，需注意长链警告 |
| 2026-06-20 | 独立 composer 服务 | FFmpeg 操作独立部署 | Docker 内网通信 `composer:8899` |
| 2026-06-21 | Code 节点 Stream 修复 | Task Runner 下 HTTP 响应为 Stream | 统一 `_outBuffer` 截断策略 |

### 1.7 API 依赖矩阵

| 服务 | 端点 | 认证方式 | 用途 |
|------|------|----------|------|
| Agnes AI | `OPENAI_BASE_URL/chat/completions` | `Bearer $OPENAI_API_KEY` | 分镜脚本生成 |
| Agnes Image | `apihub.agnes-ai.com/v1/images/generations` | `Bearer $AGNES_API_KEY` | AI 文生图 |
| Mimo TTS | `api.xiaomimimo.com/v1/chat/completions` | `api-key: $MIMO_API_KEY` | 中文 TTS 语音合成 |
| Composer | `composer:8899/compose-with-tts` | 无（内网） | FFmpeg 视频合成 |

### 1.8 文件结构速查

```
N8N-Demo03/
├── docker-compose.yml          # 主服务编排
├── Dockerfile                  # n8n 镜像（含 ffmpeg）
├── Dockerfile.composer         # 视频合成服务
├── .env                        # 密钥（不入库）
├── CODEBUDDY.md                # AI 项目指导
├── backup/                     # 工作流备份
│   └── 00-文生视频（合并版）.json
├── docs/                       # 项目文档
│   ├── project-memory-and-troubleshooting.md  # 本文档（含 Stream 修复，见 2.2.1）
│   └── *.md                     # 其他专项文档
├── scripts/
│   └── video-composer.py       # 视频合成 Python 服务
├── n8n-data/                   # n8n 持久化数据
├── n8n-files/                  # 共享文件（二进制输出）
└── Workflow/                   # 工作流 JSON 定义
```

---

## 第二部分：问题排查

### 2.1 排障黄金流程

```
发现问题
  │
  ├─ 第1步：确认范围
  │    □ n8n 实例是否运行？    → n8n_health_check
  │    □ 工作流是否激活？      → n8n_list_workflows 查 active 状态
  │    □ 环境变量是否正确？    → docker exec n8n-demo03 env | grep KEY
  │
  ├─ 第2步：获取错误上下文
  │    □ 获取最新执行 ID        → n8n_executions(action='list', limit=5)
  │    □ 查看错误详情            → n8n_executions(action='get', id=XX, mode='error')
  │    □ 检查 upstreamContext    → 确认上游节点输出是否正确
  │
  ├─ 第3步：分类诊断
  │    ├─ 节点级错误 → 见 2.2 节
  │    ├─ 连接/网络错误 → 见 2.3 节
  │    └─ 表达式/语法错误 → 见 2.4 节
  │
  └─ 第4步：修复 + 验证
       □ 使用 n8n_update_partial_workflow 增量修复
       □ 使用 n8n_validate_workflow 验证
       □ 使用 curl 触发测试
       □ 记录修复过程
```

### 2.2 常见错误模式与解决方案

#### 2.2.1 HTTP Request → Code 节点 Stream 问题 ⭐最高频

**问题现象**：Docker 部署的 n8n（Task Runner 沙箱）中，HTTP Request V4.4 节点下游的 Code 节点收到的是 Node.js Readable Stream 对象（含 `_readableState`、`_writableState`、`_outBuffer`、`_events` 等内部属性），而非解析后的 JSON。

**症状**：
```
Error: AI响应JSON解析失败 / Cannot read properties of undefined
upstreamContext.sampleItems[0].json 包含 _readableState/_writeState/_outBuffer
```

**快速诊断**：
```
n8n_executions(action='get', id=<id>, mode='error')
→ 查看 upstreamContext.sampleItems[0].json
→ 若有 _readableState 属性 → 确认是 Stream 问题
```

**✅ 方案 A：`_outBuffer` + 截断（推荐，最可靠）**

`_outBuffer` 包含从网络读取并解压缩后的完整响应体，但尾部可能有未初始化内存垃圾。

```javascript
const data = item.json;
if (data._outBuffer && data._outBuffer.data) {
  let raw = Buffer.from(data._outBuffer.data).toString('utf-8');
  // 截取到最后一个完整 JSON 对象
  const idx = raw.lastIndexOf('}');
  if (idx > 0) raw = raw.substring(0, idx + 1);
  responseText = raw;
}
```

**✅ 方案 B：`_readableState.buffer` 遍历（兜底）**

⚠️ 序列化后的 `buffer` 是普通数组（chunk 快照），不是活的 BufferList 链表。`buf.head`/`buf.tail` 为 `undefined`。

```javascript
const chunks = [];
const buf = data._readableState.buffer;
for (const chunk of buf) {
  if (chunk && chunk.data) chunks.push(Buffer.from(chunk.data));
}
responseText = Buffer.concat(chunks).toString('utf-8');
```

**✅ 方案 C：已是 JSON 对象（autodetect 可能直接解析）**

```javascript
if (data && typeof data === 'object' && (data.id || data.choices)) {
  responseText = JSON.stringify(data);
}
```

**不可用方案**

| 方案 | 原因 |
|------|------|
| `responseFormat: "file"` | `item.binary.data.data` 返回 `"filesystem-v2:..."` 引用字符串，无法 `Buffer.from()` |
| `responseFormat: "text"` | `item.json.responseBody` 行为不一致，Task Runner 下仍是 Stream |
| `$helpers.httpRequest()` | Task Runner 中 `ReferenceError: $helpers is not defined` |
| `fetch()` | Task Runner 中 `ReferenceError: fetch is not defined` |
| `require('fs')` | 仅白名单模块，Docker 默认 `NODE_FUNCTION_ALLOW_EXTERNAL` 为空 |

**附带陷阱**
- **正则中避免 `\n`**：n8n 存储/读取 Code 节点代码时，正则中的 `\n` 可能被破坏导致 `SyntaxError: missing /`。改用 `startsWith`/`endsWith`/`slice` 字符串方法替代。
- **箭头函数用 function 替代**：n8n Task Runner 对箭头函数的支持可能不稳定，优先使用 `function(s) { return ... }`。

**最佳实践**
1. HTTP Request → Code 节点的组合在 Task Runner 下是**已知脆弱模式**
2. 优先用非 Code 节点（Set、Item Lists）处理 HTTP 响应
3. 必须用 Code 节点时，统一使用 `_outBuffer` + 截断策略
4. 考虑合并 HTTP 调用到上游 Code 节点的请求构建阶段

**受影响记录**
- 工作流: `[Webhook] 00-文生视频（合并版）` (ID: `S5r7jE8tY3UJa15j`)
- 修复日期: 2026-06-21
- 受影响节点: `解析分镜输出`、`提取图片URL`、`Base64解码音频`、`检查视频结果`

---

#### 2.2.2 Webhook 数据解析失败

**症状**：`body.prompt is undefined` / `Cannot read property 'body' of undefined`

**根因**：Webhook 数据在 `$input.first().json.body`，而非顶层 `$json`。

**修复**：
```javascript
const body = $input.first().json.body || {};
// 而非：const body = $json.body;
```

---

#### 2.2.3 Code 节点返回格式错误

**症状**：下游节点收到 `undefined` 或空数据

**根因**：Code 节点必须返回 `[{json: {...}}]` 格式。

**修复**：
```javascript
return [{ json: { key: 'value' } }];  // ✅ 正确
return { key: 'value' };              // ❌ 错误
```

---

#### 2.2.4 正则表达式 SyntaxError

**症状**：`SyntaxError: missing /` 或 `Invalid regular expression`

**根因**：n8n 存储/读取 Code 节点代码时，正则中的 `\n` 可能被破坏。

**修复**：用字符串方法替代：
```javascript
// ❌ 避免
cleanContent.replace(/^```(?:json)?\n?/, '')

// ✅ 推荐
if (cleanContent.startsWith('```json')) cleanContent = cleanContent.slice(7);
else if (cleanContent.startsWith('```')) cleanContent = cleanContent.slice(3);
```

---

#### 2.2.5 API Key 无效

**症状**：HTTP 401 / 403

**排障步骤**：
```bash
# 1. 宿主机验证
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://apihub.agnes-ai.com/v1/models

# 2. 容器内验证（n8n 镜像无 curl，用 wget）
docker exec n8n-demo03 wget -qO- --header="Authorization: Bearer $OPENAI_API_KEY" \
  https://apihub.agnes-ai.com/v1/models

# 3. 确认 .env 和 docker-compose.yml 都声明了变量
```

---

#### 2.2.6 Composer 合成服务不可达

**症状**：`ECONNREFUSED` / `composer:8899` 连接失败

**检查清单**：
```bash
# 1. 确认 composer 容器运行
docker ps | grep composer

# 2. 确认同一网络
docker network inspect n8n-network

# 3. 从 n8n 容器测试连通
docker exec n8n-demo03 wget -qO- http://composer:8899/health

# 4. 检查 composer 日志
docker logs n8n-composer
```

---

### 2.3 网络/连通性排障

```bash
# 一级检查：服务运行状态
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 二级检查：容器间网络
docker exec n8n-demo03 wget -qO- --timeout=5 http://composer:8899/

# 三级检查：外部 API
docker exec n8n-demo03 wget -qO- --timeout=10 \
  --header="api-key: $MIMO_API_KEY" \
  https://api.xiaomimimo.com/v1/models

# 四级检查：n8n API
n8n_health_check
```

### 2.4 调试工具速查

| 场景 | 工具/命令 | 示例 |
|------|-----------|------|
| 查看工作流结构 | `n8n_get_workflow(id, mode='structure')` | 快速确认节点和连接 |
| 查看执行路径 | `n8n_executions(action='get', id=XX)` | 看到哪个节点失败 |
| 查看错误上下文 | `n8n_executions(action='get', id=XX, mode='error')` | 含 upstreamContext |
| Webhook 手动测试 | `curl -X POST localhost:7890/webhook/{path} -d '{...}'` | 模拟请求 |
| 容器内验证 | `docker exec n8n-demo03 wget -qO- {url}` | 网络连通性 |
| 环境变量检查 | `docker exec n8n-demo03 env \| grep KEY` | 密钥是否正确加载 |
| 工作流验证 | `n8n_validate_workflow(id)` | 部署前检查 |
| 版本回滚 | `n8n_workflow_versions` | 一键回到已知良好状态 |

### 2.5 Task Runner 沙箱限制速查

| 可用 | 不可用 |
|------|--------|
| `$input` / `$json` / `$node` | `$helpers.httpRequest()` |
| `Buffer` / `console.log` | `fetch()` |
| `JSON.parse` / `JSON.stringify` | `require()` (默认无白名单) |
| `Date` / `Math` | 第三方 npm 包 |
| String/Array 方法 | `$fromAI()` (Code 节点) |
| `NODE_FUNCTION_ALLOW_EXTERNAL=*` 后可 `require` | - |

### 2.6 恢复操作

**场景：工作流被错误修改，需要回滚**
```bash
# 1. 查看版本历史
n8n_workflow_versions(action='list', workflowId='S5r7jE8tY3UJa15j')

# 2. 回滚到指定版本
n8n_workflow_versions(action='rollback', workflowId='S5r7jE8tY3UJa15j', versionId='XXX')

# 3. 或从本地备份恢复
# backup/ 目录保存了工作流 JSON 导出
```

**场景：容器重启后 webhook 不工作**
```bash
# 1. 检查工作流是否 active
n8n_list_workflows(filter='Webhook')

# 2. 如果 active 为 false，在 n8n UI 中手动激活
# （API 不支持激活操作，需 UI 操作）
```

**场景：磁盘空间不足**
```bash
# 执行记录自动清理已启用（保留 7 天）
# 手动清理旧文件：
docker exec n8n-demo03 find /files -mtime +7 -delete
```

---

## 第三部分：变更日志

| 日期 | 变更内容 | 影响 |
|------|----------|------|
| 2026-06-21 | **文档合并**：`n8n-stream-fix-guide.md` 完整合并到本文档 2.2.1 节，消除分裂维护 | 排障文档统一入口 |
| 2026-06-21 | **Stream 修复**：4 个 Code 节点改用 `_outBuffer` 截断策略 | `00-文生视频` 全链路通 |
| 2026-06-21 | 新增本文档 | 集中管理项目记忆与排障知识 |
| 2026-06-20 | 合并子工作流为 `00-文生视频（合并版）` | 简化编排 |
| 2026-06-20 | 新增 composer 视频合成服务 | 独立 FFmpeg 操作 |
| 2026-06-14 | 初始化项目，Docker 部署 n8n v2.5.0 | 项目起点 |

---

> **维护原则**：每次遇到新问题并解决后，立即更新本文档的 2.2 节（错误模式）和 1.6 节（决策记录）。文档越全，下次排障越快。
