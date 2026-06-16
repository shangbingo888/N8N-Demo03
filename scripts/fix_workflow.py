#!/usr/bin/env python3
"""Fix corrupted nodes in workflow CHK27Wm9JjlUZ83U"""
import json, urllib.request, urllib.error

API = "http://localhost:7890"
KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyMDM1OGZiNy0xMzQ0LTQwMmItOTc5MS00OTg3YjllNDNkZTEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMTRhOWY4YmEtYmQzNC00MWZiLTkxMWEtNmIxN2Q4ZGViMWZkIiwiaWF0IjoxNzgxNDM4MDIxfQ.9nr2Yjlc7Ic5v6YGZvEMH-FNI2jvpmHYdwpFEnhxdBA"
WF_ID = "CHK27Wm9JjlUZ83U"

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

# 1. Get current workflow
wf = api(f"/api/v1/workflows/{WF_ID}")

# 2. Fix corrupted nodes
for node in wf["nodes"]:
    if node["name"] == "Base64解码为二进制":
        node["parameters"]["jsCode"] = """const mimoResponse = $input.first().json;
const base64Audio = mimoResponse.choices[0].message.audio.data;
const audioBuffer = Buffer.from(base64Audio, 'base64');

return [{
  json: { audioSize: audioBuffer.length, format: 'wav' },
  binary: {
    data: {
      data: audioBuffer.toString('base64'),
      mimeType: 'audio/wav',
      fileName: 'speech.wav'
    }
  }
}];"""
        print("✅ Fixed: Base64解码为二进制")

    if node["name"] == "保存音频文件":
        node["parameters"]["fileName"] = "=/data/audio/speech_{{ $now.format('yyyyMMdd_HHmmss') }}.wav"
        print("✅ Fixed: 保存音频文件")

# 3. Update workflow
result = api(f"/api/v1/workflows/{WF_ID}", method="PUT", data={
    "name": wf["name"],
    "nodes": wf["nodes"],
    "connections": wf["connections"],
    "settings": wf["settings"]
})
print(f"✅ Updated: {result['id']} | active: {result['active']} | version: {result['versionCounter']}")
