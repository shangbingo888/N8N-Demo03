#!/usr/bin/env python3
"""将工作流从 OpenAI TTS 适配为 Mimo TTS API v2.5"""

import json, urllib.request, urllib.error

N8N_URL = "http://localhost:7890"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwOGIyYTIyOS01NjcwLTRiYzItOGI5ZS0xZDhmOTJkNzQ5NTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMDE3MDQ1YjMtZWVkZi00MjA4LTk2ZWYtNDMzNDc1NjQ5NDQzIiwiaWF0IjoxNzgxNDM4OTk4fQ.ThqbaBj03mvBqAJ_L1MfoFeOVOjJFsfeXsXwIajLsaQ"
WF_ID = "9YFnCngyMUs5eJEp"

def api(method, path, data=None):
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

# 获取当前工作流
wf, code = api("GET", f"/workflows/{WF_ID}")
if code != 200:
    print(f"❌ 获取失败: {code}")
    exit(1)

print(f"✅ 获取工作流: {wf['name']}")

# ============================================================
# Mimo TTS API 请求 body（JSON 字符串格式）
# ============================================================
MIMO_BODY = """={
  "model": "mimo-v2.5-tts",
  "messages": [
    {
      "role": "user",
      "content": "用自然亲切的语气播报"
    },
    {
      "role": "assistant",
      "content": "{{ $json.body.text }}"
    }
  ],
  "audio": {
    "format": "wav",
    "voice": "{{ $json.body.voice || '冰糖' }}"
  },
  "stream": false
}"""

# ============================================================
# Code 节点 - Base64 WAV → Binary
# ============================================================
DECODE_JS = """// Mimo TTS 返回 Base64 WAV → 解码为二进制
const items = [];

for (const item of $input.all()) {
  const choice = item.json?.choices?.[0];
  const audioData = choice?.message?.audio?.data;
  
  if (!audioData) {
    throw new Error(
      'Mimo TTS 返回异常: ' + 
      JSON.stringify(item.json).substring(0, 300)
    );
  }
  
  const inputText = $('接收文本输入').first().json.body.text;
  
  items.push({
    json: {
      inputText: inputText,
      voice: $('接收文本输入').first().json.body.voice || '冰糖',
      status: 'success',
      textLength: inputText.length
    },
    binary: {
      data: {
        data: Buffer.from(audioData, 'base64'),
        mimeType: 'audio/wav',
        fileName: 'mimo-tts-output.wav'
      }
    }
  });
}

return items;"""

# ============================================================
# 构建新节点列表
# ============================================================
new_nodes = []
for node in wf["nodes"]:
    if node["name"] in ["mimo", "OpenAI 生成音频"]:
        continue  # 移除旧的 OpenAI 节点
    elif node["name"] == "保存音频文件":
        node["parameters"]["fileName"] = "/tmp/n8n-mimo-tts.wav"
        new_nodes.append(node)
    else:
        new_nodes.append(node)

# HTTP Request - 调用 Mimo API (插入到 index 1，Webhook 之后)
http_req = {
    "id": "mimo-http-request",
    "name": "请求 Mimo TTS API",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.2,
    "position": [600, 300],
    "parameters": {
        "method": "POST",
        "url": "https://api.xiaomimimo.com/v1/chat/completions",
        "sendHeaders": True,
        "headerParameters": {
            "parameters": [
                {
                    "name": "api-key",
                    "value": "={{ $credentials.mimoApiKey }}"
                }
            ]
        },
        "sendBody": True,
        "contentType": "raw",
        "rawContentType": "application/json",
        "body": MIMO_BODY,
        "options": {
            "timeout": 60000,
            "response": {
                "response": {
                    "responseFormat": "json"
                }
            }
        }
    }
}

# Code 节点 - Base64 解码 (插入到 index 2)
code_node = {
    "id": "mimo-decode",
    "name": "Base64 解码为音频文件",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [980, 300],
    "parameters": {
        "jsCode": DECODE_JS
    }
}

new_nodes.insert(1, http_req)
new_nodes.insert(2, code_node)

# ============================================================
# 连接关系
# ============================================================
new_connections = {
    "接收文本输入": {
        "main": [[{"node": "请求 Mimo TTS API", "type": "main", "index": 0}]]
    },
    "请求 Mimo TTS API": {
        "main": [
            [{"node": "Base64 解码为音频文件", "type": "main", "index": 0}],
            [{"node": "错误处理", "type": "main", "index": 0}]
        ]
    },
    "Base64 解码为音频文件": {
        "main": [
            [{"node": "保存音频文件", "type": "main", "index": 0}],
            [{"node": "错误处理", "type": "main", "index": 0}]
        ]
    },
    "保存音频文件": {
        "main": [[{"node": "返回音频给调用方", "type": "main", "index": 0}]]
    }
}

# ============================================================
# 提交
# ============================================================
update_data = {
    "name": "[Webhook] 文本转音频 - Mimo TTS v2.5",
    "nodes": new_nodes,
    "connections": new_connections,
    "settings": wf.get("settings", {})
}

print(f"\n📋 新节点: {[n['name'] for n in new_nodes]}")
resp, code = api("PUT", f"/workflows/{WF_ID}", update_data)

if code in (200, 201):
    print("\n✅ 工作流已适配 Mimo TTS v2.5！")
    print("=" * 60)
    print("""
┌──────────────────┐
│  Webhook 触发器    │  POST /text-to-audio
│  接收文本输入       │  {"text":"...", "voice":"冰糖"}
└────────┬─────────┘
         ▼
┌──────────────────────────────────────┐
│  请求 Mimo TTS API (HTTP Request)     │
│  POST api.xiaomimimo.com/v1/chat/... │
│  model: mimo-v2.5-tts  format: wav  │
│  认证: Header api-key                │
└────────┬─────────────────────────────┘
         │  { choices[0].message.audio.data (Base64) }
         ▼
┌──────────────────────┐
│  Base64 解码为音频     │  Buffer.from(base64,'base64')
│  (Code 节点)          │  → binary WAV
└────┬─────────┬───────┘
     │         │ 失败
     ▼         ▼
┌────────┐ ┌──────────┐
│保存.wav│ │ 错误处理  │
└───┬────┘ └──────────┘
    ▼
┌──────────────┐
│ Respond to   │  返回 WAV 二进制
│ Webhook      │
└──────────────┘
""")
    print("=" * 60)
    print(f"📝 编辑地址: {N8N_URL}/workflow/{WF_ID}")
    print()
    print("⚠️  配置 Mimo API 凭据（必做）：")
    print("   1. 打开编辑页面，双击「请求 Mimo TTS API」节点")
    print("   2. 在 Credentials 中添加 Mimo API Key:")
    print("      https://platform.xiaomimimo.com")
    print()
    print("🧪 配置完成后测试:")
    print(f'   curl -X POST "{N8N_URL}/webhook-test/text-to-audio" \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -d \'{{"text":"你好世界"}}\' \\')
    print(f'     --output mimo-test.wav')
    print(f'   afplay mimo-test.wav')
    print()
    print("🎤 可选音色: 冰糖(默认) | 茉莉 | 苏打 | 白桦 | Mia | Chloe | Milo | Dean")

else:
    print(f"\n❌ 失败 HTTP {code}")
    print(json.dumps(resp, indent=2, ensure_ascii=False)[:800])
