#!/usr/bin/env python3
"""Create n8n workflow with Webhook trigger"""
import json, urllib.request, urllib.error, time

API = "http://localhost:7890"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyMDM1OGZiNy0xMzQ0LTQwMmItOTc5MS00OTg3YjllNDNkZTEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMTRhOWY4YmEtYmQzNC00MWZiLTkxMWEtNmIxN2Q4ZGViMWZkIiwiaWF0IjoxNzgxNDM4MDIxfQ.9nr2Yjlc7Ic5v6YGZvEMH-FNI2jvpmHYdwpFEnhxdBA"

def api(path, method="GET", data=None):
    url = f"{API}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("X-N8N-API-KEY", KEY)
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.read().decode()[:300]}")
        raise

# Clean up
for old_id in ["CHK27Wm9JjlUZ83U", "2eIIaxwk26MUcFfv", "SefyBKVAFi8osl92"]:
    try:
        api(f"/api/v1/workflows/{old_id}", method="DELETE")
    except:
        pass

workflow = {
    "name": "[Webhook] 文字→DeepSeek文案→Mimo语音",
    "nodes": [
        {
            "id": "webhook-trigger",
            "name": "接收文本Prompt",
            "type": "n8n-nodes-base.webhook",
            "typeVersion": 1,
            "position": [0, 0],
            "parameters": {
                "httpMethod": "POST",
                "path": "text-to-speech",
                "responseMode": "lastNode",
                "options": {}
            }
        },
        {
            "id": "ai-agent",
            "name": "AI Agent",
            "type": "@n8n/n8n-nodes-langchain.agent",
            "typeVersion": 3.1,
            "position": [240, 0],
            "parameters": {
                "promptType": "define",
                "text": "你是一个专业的短视频文案写手。根据用户的主题描述，生成一段适合语音朗读的短视频文案。\n\n要求：\n1. 30-60秒朗读时长（约80-150字）\n2. 语言自然流畅，适合中文口语表达\n3. 节奏紧凑，有画面感\n4. 只输出文案内容，不要任何解释、标题或前缀"
            }
        },
        {
            "id": "deepseek-model",
            "name": "DeepSeek Chat Model",
            "type": "@n8n/n8n-nodes-langchain.lmChatDeepSeek",
            "typeVersion": 1,
            "position": [200, 230],
            "parameters": {
                "model": "deepseek-chat",
                "options": {}
            },
            "credentials": {
                "deepSeekApi": {
                    "id": "MTrTjTsoDOIg0XIa",
                    "name": "DeepSeek account 2"
                }
            }
        },
        {
            "id": "build-mimo-body",
            "name": "构造Mimo请求体",
            "type": "n8n-nodes-base.code",
            "typeVersion": 1,
            "position": [480, 0],
            "parameters": {
                "jsCode": "const copywriting = $input.first().json.output;\n\nconst mimoBody = {\n  model: \"mimo-v2.5-tts\",\n  messages: [\n    { role: \"user\", content: \"用温柔亲切的语调朗读，语速适中，像在和朋友聊天一样自然\" },\n    { role: \"assistant\", content: copywriting }\n  ],\n  audio: { format: \"wav\", voice: \"冰糖\" },\n  stream: false\n};\n\nreturn [{\n  json: {\n    mimoBody: mimoBody,\n    copywriting: copywriting,\n    mimoBodyString: JSON.stringify(mimoBody)\n  }\n}];"
            }
        },
        {
            "id": "call-mimo-tts",
            "name": "调用Mimo语音合成",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4,
            "position": [720, 0],
            "parameters": {
                "url": "https://api.xiaomimimo.com/v1/chat/completions",
                "method": "POST",
                "authentication": "none",
                "sendBody": True,
                "contentType": "raw",
                "rawContent": "={{ $json.mimoBodyString }}",
                "sendHeaders": True,
                "headerParameters": {
                    "parameters": [
                        {"name": "api-key", "value": "=tp-cgtivp94l7ijvurssdnfah1dwy4jq23d5kbbqzacyld3cmov"},
                        {"name": "Content-Type", "value": "application/json"}
                    ]
                },
                "options": {
                    "timeout": 120000,
                    "response": {"response": {"responseFormat": "json"}}
                }
            }
        },
        {
            "id": "decode-base64",
            "name": "Base64解码为二进制",
            "type": "n8n-nodes-base.code",
            "typeVersion": 1,
            "position": [960, 0],
            "parameters": {
                "jsCode": "const mimoResponse = $input.first().json;\nconst base64Audio = mimoResponse.choices[0].message.audio.data;\nconst audioBuffer = Buffer.from(base64Audio, 'base64');\n\nreturn [{\n  json: { audioSize: audioBuffer.length, format: 'wav' },\n  binary: {\n    data: {\n      data: audioBuffer.toString('base64'),\n      mimeType: 'audio/wav',\n      fileName: 'speech.wav'\n    }\n  }\n}];"
            }
        },
        {
            "id": "save-audio-file",
            "name": "保存音频文件",
            "type": "n8n-nodes-base.writeBinaryFile",
            "typeVersion": 1,
            "position": [1200, 0],
            "parameters": {
                "fileName": "=/data/audio/speech_{{ $now.format('yyyyMMdd_HHmmss') }}.wav",
                "dataPropertyName": "data",
                "options": {}
            }
        }
    ],
    "connections": {
        "接收文本Prompt": {"main": [[{"node": "AI Agent", "type": "main", "index": 0}]]},
        "AI Agent": {"main": [[{"node": "构造Mimo请求体", "type": "main", "index": 0}]]},
        "DeepSeek Chat Model": {"ai_languageModel": [[{"node": "AI Agent", "type": "ai_languageModel", "index": 0}]]},
        "构造Mimo请求体": {"main": [[{"node": "调用Mimo语音合成", "type": "main", "index": 0}]]},
        "调用Mimo语音合成": {"main": [[{"node": "Base64解码为二进制", "type": "main", "index": 0}]]},
        "Base64解码为二进制": {"main": [[{"node": "保存音频文件", "type": "main", "index": 0}]]}
    },
    "settings": {
        "executionOrder": "v1",
        "saveDataErrorExecution": "all",
        "saveDataSuccessExecution": "all",
        "saveManualExecutions": True
    }
}

result = api("/api/v1/workflows", method="POST", data=workflow)
wf_id = result["id"]
print(f"✅ Created: {wf_id} | {result['name']}")

api(f"/api/v1/workflows/{wf_id}/activate", method="POST")
print("   Active: True")

time.sleep(1)
wf = api(f"/api/v1/workflows/{wf_id}")
wh_node = wf["nodes"][0]
wh_id = wh_node.get("webhookId", "NONE")
print(f"   webhookId: {wh_id}")

# Test webhook
if wh_id != "NONE":
    import urllib.request as ur
    data = json.dumps({"prompt": "写一段30秒的AI改变生活短视频文案"}).encode()
    req = ur.Request(f"{API}/webhook/text-to-speech", data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with ur.urlopen(req, timeout=30) as r:
            print(f"   Webhook test: HTTP {r.status}")
    except ur.HTTPError as e:
        print(f"   Webhook test: HTTP {e.code}")
    except Exception as e:
        print(f"   Webhook test error: {e[:50]}...")

print(f"\n📋 curl 触发命令:")
print(f"   curl -X POST {API}/webhook/text-to-speech -H 'Content-Type: application/json' -d '{{\"prompt\":\"写一段30秒的AI科技短视频文案\"}}'")
