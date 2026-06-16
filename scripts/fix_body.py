import json, urllib.request

API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwOGIyYTIyOS01NjcwLTRiYzItOGI5ZS0xZDhmOTJkNzQ5NTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMDE3MDQ1YjMtZWVkZi00MjA4LTk2ZWYtNDMzNDc1NjQ5NDQzIiwiaWF0IjoxNzgxNDM4OTk4fQ.ThqbaBj03mvBqAJ_L1MfoFeOVOjJFsfeXsXwIajLsaQ'
WF_ID = 'Yx6HEeubylg10sVh'
N8N = 'http://localhost:7890'

req = urllib.request.Request(f'{N8N}/api/v1/workflows/{WF_ID}', headers={'X-N8N-API-KEY': API_KEY})
with urllib.request.urlopen(req) as resp:
    wf = json.loads(resp.read())

for node in wf['nodes']:
    if node['name'] == '调用Mimo语音合成':
        old = node['parameters'].get('body', 'NONE')
        new_body = '={{ JSON.stringify($json.mimoBody) }}'
        print(f'旧 body: {old}')
        print(f'新 body: {new_body}')
        node['parameters']['body'] = new_body
        break

update = {'name': wf['name'], 'nodes': wf['nodes'], 'connections': wf['connections'], 'settings': wf.get('settings', {})}
data = json.dumps(update).encode()
req = urllib.request.Request(f'{N8N}/api/v1/workflows/{WF_ID}', data=data, headers={'X-N8N-API-KEY': API_KEY, 'Content-Type': 'application/json'}, method='PUT')
with urllib.request.urlopen(req) as resp:
    print(f'✅ HTTP {resp.status}')
