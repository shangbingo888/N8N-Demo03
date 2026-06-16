#!/usr/bin/env python3
"""完善工作流：添加错误连接和重试设置"""

import json
import urllib.request
import urllib.error

N8N_URL = "http://localhost:7890"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwOGIyYTIyOS01NjcwLTRiYzItOGI5ZS0xZDhmOTJkNzQ5NTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMDE3MDQ1YjMtZWVkZi00MjA4LTk2ZWYtNDMzNDc1NjQ5NDQzIiwiaWF0IjoxNzgxNDM4OTk4fQ.ThqbaBj03mvBqAJ_L1MfoFeOVOjJFsfeXsXwIajLsaQ"
WF_ID = "9YFnCngyMUs5eJEp"

def api_call(method, path, data=None):
    url = f"{N8N_URL}/api/v1{path}"
    headers = {"X-N8N-API-KEY": API_KEY, "Content-Type": "application/json"}
    req_data = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return json.loads(body) if body else {"error": str(e)}, e.code

# Step 1: 获取当前工作流
print("Step 1: 获取当前工作流...")
wf, code = api_call("GET", f"/workflows/{WF_ID}")
if code != 200:
    print(f"❌ 获取失败: {code} {wf}")
    exit(1)
print(f"✅ 获取成功: {wf.get('name')}")

# Step 2: 使用 n8n 原生 API 添加错误连接
# 给 OpenAI 节点添加 error output 连接到错误处理节点
print("\nStep 2: 更新工作流 - 添加错误处理连接...")

# 直接使用 full update
nodes = wf.get("nodes", [])
connections = wf.get("connections", {})

# 为 OpenAI 节点添加 error 连接
connections["OpenAI 生成音频"] = {
    "main": [
        [{"node": "保存音频文件", "type": "main", "index": 0}],
        [{"node": "错误处理", "type": "main", "index": 0}]  # error output
    ]
}

update_data = {
    "name": wf["name"],
    "nodes": nodes,
    "connections": connections,
    "settings": wf.get("settings", {"saveManualExecutions": True})
}

resp, code = api_call("PUT", f"/workflows/{WF_ID}", update_data)
if code in (200, 201):
    print("✅ 工作流更新成功！")
    
    # 显示连接情况
    conn = resp.get("connections", {})
    for node_name, node_conns in conn.items():
        main_count = len(node_conns.get("main", []))
        print(f"  🔗 {node_name}: {main_count} 个输出端口")
        for i, outputs in enumerate(node_conns.get("main", [])):
            for o in outputs:
                target = o.get("node", "?")
                port_type = "主输出" if i == 0 else "错误输出"
                print(f"       → {target} ({port_type})")
else:
    print(f"❌ 更新失败: {code}")
    print(json.dumps(resp, indent=2, ensure_ascii=False)[:500])
    exit(1)

# Step 3: 显示完整的工作流结构
print("\n" + "=" * 60)
print("📋 最终工作流结构")
print("=" * 60)
print("""
  ┌─────────────────┐
  │  Webhook 触发器   │  POST /webhook/text-to-audio
  │  接收文本输入     │  接收 {"text": "..."}
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  OpenAI 音频生成  │  resource=audio, voice=nova
  │  (LangChain)     │  input: $json.body.text
  └────┬───────┬────┘
       │       │
  成功  │       │  失败
       ▼       ▼
  ┌────────┐ ┌──────────┐
  │ 保存文件│ │ 错误处理  │
  │ .mp3   │ │ 停止+通知 │
  └───┬────┘ └──────────┘
      │
      ▼
  ┌──────────────┐
  │ 响应 Webhook  │  返回 MP3 二进制文件
  │  返回音频     │
  └──────────────┘
""")

print("\n⚠️  重要提醒：")
print("  1. 在 n8n UI 中为 'OpenAI 生成音频' 节点配置 OpenAI 凭据")
print(f"     编辑地址: {N8N_URL}/workflow/{WF_ID}")
print("  2. 配置完成后，点击右上角开关激活工作流")
print("  3. 测试命令：")
print(f'     curl -X POST "{N8N_URL}/webhook-test/text-to-audio" \\')
print(f'       -H "Content-Type: application/json" \\')
print(f"       -d '{{\"text\": \"你好，欢迎来到 n8n 自动化世界！\"}}' \\")
print(f"       --output test-output.mp3")
print(f"  4. 播放测试音频:  afplay test-output.mp3")
