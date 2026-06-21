#!/bin/bash
# 重启 n8n 容器以应用 N8N_BLOCK_LOCAL_ADDRESS_ACCESS=false 配置
# 此配置允许工作流内部通过 localhost 调用子工作流

cd "$(dirname "$0")/.."

echo "=== 重启 n8n 容器 ==="
docker compose restart n8n

echo ""
echo "=== 等待 n8n 启动 ==="
sleep 5

# 健康检查
echo "=== 健康检查 ==="
for i in 1 2 3 4 5 6; do
  if curl -sf http://localhost:7890/healthz > /dev/null 2>&1; then
    echo "✅ n8n 已就绪"
    break
  fi
  echo "等待中... ($i/6)"
  sleep 5
done

echo ""
echo "=== 确认 SSRF 配置 ==="
docker exec n8n-demo03 wget -qO- http://localhost:5678/healthz 2>&1 && echo "✅ 容器内 localhost 可达" || echo "⚠️ 容器内 localhost 不可达"

echo ""
echo "=== 确认子工作流状态 ==="
curl -s http://localhost:7890/api/v1/workflows/JjMxOUIMgJBpwxer \
  -H "X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwOGIyYTIyOS01NjcwLTRiYzItOGI5ZS0xZDhmOTJkNzQ5NTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMDE3MDQ1YjMtZWVkZi00MjA4LTk2ZWYtNDMzNDc1NjQ5NDQzIiwiaWF0IjoxNzgxNDM4OTk4fQ.ThqbaBj03mvBqAJ_L1MfoFeOVOjJFsfeXsXwIajLsaQ" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'01-分镜: active={d.get(\"active\",\"?\")}')" 2>/dev/null

curl -s http://localhost:7890/api/v1/workflows/iD87BeQkqIZCLWiM \
  -H "X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwOGIyYTIyOS01NjcwLTRiYzItOGI5ZS0xZDhmOTJkNzQ5NTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMDE3MDQ1YjMtZWVkZi00MjA4LTk2ZWYtNDMzNDc1NjQ5NDQzIiwiaWF0IjoxNzgxNDM4OTk4fQ.ThqbaBj03mvBqAJ_L1MfoFeOVOjJFsfeXsXwIajLsaQ" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'02-生图: active={d.get(\"active\",\"?\")}')" 2>/dev/null

curl -s http://localhost:7890/api/v1/workflows/7aA8FNq2ixjuphuX \
  -H "X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwOGIyYTIyOS01NjcwLTRiYzItOGI5ZS0xZDhmOTJkNzQ5NTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMDE3MDQ1YjMtZWVkZi00MjA4LTk2ZWYtNDMzNDc1NjQ5NDQzIiwiaWF0IjoxNzgxNDM4OTk4fQ.ThqbaBj03mvBqAJ_L1MfoFeOVOjJFsfeXsXwIajLsaQ" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'03-TTS: active={d.get(\"active\",\"?\")}')" 2>/dev/null

echo ""
echo "=== 完成 ==="
echo "可以运行测试: curl -X POST http://localhost:7890/webhook-test/test-main-orchestrator -H 'Content-Type: application/json' -d '{\"provider\":\"openai\",\"topic\":\"测试\"}'"
