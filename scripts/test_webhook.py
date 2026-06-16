#!/usr/bin/env python3
"""Test webhook then create full workflow"""
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
        body = e.read().decode()[:300]
        print(f"  HTTP {e.code}: {body}")
        return None

# Step 1: Create test webhook, activate, test
print("=== Phase 1: Test webhook registration ===")
r = api("/api/v1/workflows", "POST", {
    "name": "webhook-test",
    "nodes": [{
        "id": "w", "name": "Webhook", "type": "n8n-nodes-base.webhook",
        "typeVersion": 1, "position": [0,0],
        "parameters": {"httpMethod": "POST", "path": "ping", "responseMode": "lastNode", "options": {}}
    }],
    "connections": {},
    "settings": {"executionOrder": "v1"}
})
if not r:
    print("❌ Create failed - user needs to setup n8n account first")
    print("   Go to http://localhost:7890, create account, then update API key in .mcp.json")
    exit(1)

wf_id = r["id"]
print(f"   Created: {wf_id}")

# Deactivate first (if active), then activate  
api(f"/api/v1/workflows/{wf_id}/deactivate", "POST")

# Check if account setup needed
time.sleep(1)
r2 = api(f"/api/v1/workflows/{wf_id}/activate", "POST")
if not r2:
    print("❌ Activate failed - likely need to setup n8n account first")
    exit(1)

print(f"   Active: {r2.get('active', '?')}")
time.sleep(2)

# Test webhook
print("   Testing /webhook/ping...")
try:
    req = urllib.request.Request(f"{API}/webhook/ping", data=json.dumps({"test":1}).encode(), method="POST")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"   ✅ Webhook working! HTTP {resp.status}")
except urllib.error.HTTPError as e:
    print(f"   HTTP {e.code}: {e.read().decode()[:200]}")
except Exception as e:
    print(f"   Error: {e}")

# Clean up test
api(f"/api/v1/workflows/{wf_id}", "DELETE")

print("\n=== Phase 2: Create full workflow ===")
# Check if webhook worked, then proceed
