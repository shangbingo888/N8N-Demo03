import json, urllib.request

API_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwOGIyYTIyOS01NjcwLTRiYzItOGI5ZS0xZDhmOTJkNzQ5NTYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiMDE3MDQ1YjMtZWVkZi00MjA4LTk2ZWYtNDMzNDc1NjQ5NDQzIiwiaWF0IjoxNzgxNDM4OTk4fQ.ThqbaBj03mvBqAJ_L1MfoFeOVOjJFsfeXsXwIajLsaQ'
WF_ID = 'Yx6HEeubylg10sVh'

req = urllib.request.Request('http://localhost:7890/api/v1/workflows/' + WF_ID, headers={'X-N8N-API-KEY': API_KEY})
with urllib.request.urlopen(req) as resp:
    wf = json.loads(resp.read())

new_code = """const item = $input.first();

// HTTP Request v4 可能把响应存为二进制数据而非 JSON
// 检查 binary 属性
let responseText;
if (item.binary?.data?.data) {
  responseText = item.binary.data.data.toString('utf8');
} else if (item.json?.body) {
  responseText = item.json.body;
} else if (typeof item.json === 'string') {
  responseText = item.json;
} else {
  responseText = JSON.stringify(item.json);
}

let mimoResponse;
try {
  mimoResponse = JSON.parse(responseText);
} catch (e) {
  throw new Error('Response not JSON: ' + responseText.substring(0, 500));
}

if (mimoResponse.error) {
  throw new Error('Mimo API error: ' + JSON.stringify(mimoResponse.error));
}

const base64Audio = mimoResponse.choices?.[0]?.message?.audio?.data;
if (!base64Audio) {
  throw new Error('No audio in response. Keys: ' + JSON.stringify(Object.keys(mimoResponse)).substring(0, 300));
}

const audioBuffer = Buffer.from(base64Audio, 'base64');
return [{json: {audioSize: audioBuffer.length, format: 'wav'}, binary: {data: {data: audioBuffer.toString('base64'), mimeType: 'audio/wav', fileName: 'speech.wav'}}}];"""

for node in wf['nodes']:
    if node['name'] == 'Base64解码为二进制':
        node['parameters']['jsCode'] = new_code
        print('✅ 已更新解码代码（兼容多种响应格式）')
        break

update = {'name': wf['name'], 'nodes': wf['nodes'], 'connections': wf['connections'], 'settings': wf.get('settings', {})}
data = json.dumps(update).encode()
req = urllib.request.Request('http://localhost:7890/api/v1/workflows/' + WF_ID, data=data, headers={'X-N8N-API-KEY': API_KEY, 'Content-Type': 'application/json'}, method='PUT')
with urllib.request.urlopen(req) as resp:
    print(f'✅ HTTP {resp.status}')
