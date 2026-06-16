#!/usr/bin/env python3
"""创建 '文本转音频' 工作流并通过 n8n API 部署"""

import json
import urllib.request
import urllib.error

N8N_URL = "http://localhost:7890"
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwOGIyYTIyOS01NjcwLTRiYzItOGI5ZS0xZDhmOTJkNzQ5NTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMDE3MDQ1YjMtZWVkZi00MjA4LTk2ZWYtNDMzNDc1NjQ5NDQzIiwiaWF0IjoxNzgxNDM4OTk4fQ.ThqbaBj03mvBqAJ_L1MfoFeOVOjJFsfeXsXwIajLsaQ"

workflow = {
    "name": "[Webhook] 文本转音频 - OpenAI TTS",
    "nodes": [
        {
            "id": "webhook-trigger",
            "name": "接收文本输入",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 2.1,
            "position": [250, 300],
            "parameters": {
                "httpMethod": "POST",
                "path": "text-to-audio",
                "responseMode": "responseNode",
                "options": {}
            }
        },
        {
            "id": "openai-tts",
            "name": "OpenAI 生成音频",
            "type": "@n8n/n8n-nodes-langchain.openAi",
            "typeVersion": 2.1,
            "position": [600, 300],
            "parameters": {
                "resource": "audio",
                "operation": "generate",
                "input": "={{ $json.body.text }}",
                "voice": "nova",
                "options": {
                    "speed": 1
                }
            }
        },
        {
            "id": "save-file",
            "name": "保存音频文件",
            "type": "n8n-nodes-base.writeBinaryFile",
            "typeVersion": 1,
            "position": [950, 300],
            "parameters": {
                "fileName": "/tmp/n8n-tts-output.mp3",
                "dataPropertyName": "data"
            }
        },
        {
            "id": "respond",
            "name": "返回音频给调用方",
            "type": "n8n-nodes-base.respondToWebhook",
            "typeVersion": 1.5,
            "position": [1300, 300],
            "parameters": {
                "respondWith": "binary",
                "inputFieldName": "data",
                "options": {}
            }
        },
        {
            "id": "error-handler",
            "name": "错误处理",
            "type": "n8n-nodes-base.stopAndError",
            "typeVersion": 1,
            "position": [950, 550],
            "parameters": {
                "message": "音频生成失败，请检查 OpenAI 凭据和输入文本"
            }
        }
    ],
    "connections": {
        "接收文本输入": {
            "main": [
                [
                    {"node": "OpenAI 生成音频", "type": "main", "index": 0}
                ]
            ]
        },
        "OpenAI 生成音频": {
            "main": [
                [
                    {"node": "保存音频文件", "type": "main", "index": 0}
                ]
            ]
        },
        "保存音频文件": {
            "main": [
                [
                    {"node": "返回音频给调用方", "type": "main", "index": 0}
                ]
            ]
        }
    },
    "settings": {
        "saveManualExecutions": True,
        "timezone": "Asia/Shanghai"
    }
}

def api_call(method, path, data=None):
    url = f"{N8N_URL}/api/v1{path}"
    headers = {
        "X-N8N-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }
    req_data = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()), resp.status
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        return json.loads(body) if body else {"error": str(e)}, e.code

# Step 1: 创建工作流
print("=" * 60)
print("Step 1: 创建工作流...")
resp, code = api_call("POST", "/workflows", workflow)

if code in (200, 201):
    wf_id = resp.get("id", resp.get("data", {}).get("id", ""))
    wf_name = resp.get("name", resp.get("data", {}).get("name", ""))
    print(f"✅ 工作流已创建! ID: {wf_id}, Name: {wf_name}")
    print(f"   编辑地址: {N8N_URL}/workflow/{wf_id}")
    
    # Step 2: 验证工作流
    print("\n" + "=" * 60)
    print("Step 2: 验证工作流...")
    
    # Check for errors
    if resp.get("active") or resp.get("data", {}).get("active"):
        print("⚠️  工作流已激活（生产 Webhook 可用）")
    
    print(f"\n工作流详情:")
    nodes = resp.get("nodes", resp.get("data", {}).get("nodes", []))
    for node in nodes:
        name = node.get("name", "Unknown")
        ntype = node.get("type", "Unknown")
        print(f"  📦 {name} ({ntype})")
    
    print(f"\n📋 节点数: {len(nodes)}")
    print(f"🔗 连接数: {len(resp.get('connections', resp.get('data', {}).get('connections', {})))} 组")
    
    # Step 3: 显示测试命令
    print("\n" + "=" * 60)
    print("Step 3: 测试方法")
    print("-" * 40)
    print("测试模式 (工作流未激活时):")
    print(f"  curl -X POST '{N8N_URL}/webhook-test/text-to-audio' \\")
    print(f"    -H 'Content-Type: application/json' \\")
    print(f"    -d '{{\"text\": \"你好，这是来自 n8n 的第一条语音消息！\"}}' \\")
    print(f"    --output test-output.mp3")
    print()
    print("生产模式 (工作流激活后):")
    print(f"  curl -X POST '{N8N_URL}/webhook/text-to-audio' \\")
    print(f"    -H 'Content-Type: application/json' \\")
    print(f"    -d '{{\"text\": \"你好，这是来自 n8n 的语音！\"}}' \\")
    print(f"    --output test-output.mp3")
    
else:
    print(f"❌ 创建失败! HTTP {code}")
    print(json.dumps(resp, indent=2, ensure_ascii=False))
