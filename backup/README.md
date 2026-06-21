# 备份快照 — 2026-06-20 11:13

## 管道架构

```
curl → n8n(localhost:7890/webhook/merged-pipeline)
         │
         ├─→ AI 分镜 (Agnes AI) → 5 场景 + 旁白
         ├─→ 图片生成 (Agnes Image) → HTTP URL
         ├─→ TTS 提取 (Mimo API) → 在 n8n 内解码
         │
         └─→ 合成服务 (composer:8899/compose-with-tts)
              ├─→ 下载图片 (从 URL)
              ├─→ Mimo TTS 配音
              ├─→ FFmpeg 合成 MP4
              └─→ 保存到 /files/ 共享卷
```

## 文件说明

| 文件 | 用途 |
|------|------|
| `docker-compose.yml` | 主配置：n8n + composer 双服务 |
| `Dockerfile` | n8n 镜像 (含 FFmpeg) |
| `Dockerfile.composer` | 合成服务镜像 (Python + FFmpeg) |
| `.env` | API 密钥（勿提交 Git） |
| `.env.example` | API 密钥模板 |
| `video-composer.py` | 合成服务源码 |
| `merged-pipeline-active.json` | 当前激活的 n8n 工作流 |
| `00-主编排-文生视频.json` | 旧版主管工作流（Manual 触发） |
| `01~04-*.json` | 子工作流（分镜/生图/TTS/合成） |
| `current_state.json` | 旧版备份状态 |
| `workflow.json` | 旧版工作流导出 |

## Docker 服务

```bash
# 启动
docker compose up -d

# 状态
docker compose ps
# n8n-demo03    → localhost:7890 (n8n Webhook)
# n8n-composer  → localhost:8899 (合成服务 + 文件下载)

# 生成视频
curl -X POST http://localhost:7890/webhook/merged-pipeline \
  -H "Content-Type: application/json" \
  -d '{"provider":"openai","topic":"你的主题"}'
```
