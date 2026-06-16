#!/bin/bash
# Mimo TTS API 直连测试 —— 先验证 API 再在 n8n 建工作流
# 用法: ./test_mimo_api.sh "你好世界"
#        ./test_mimo_api.sh "Hello world" "Mia"

TEXT="${1:-你好世界，这是测试文本}"
VOICE="${2:-冰糖}"
KEY="YOUR_MIMO_KEY"

echo "========== Mimo TTS 测试 =========="
echo "文本: $TEXT"
echo "音色: $VOICE"
echo ""

RESP=$(curl -s -w "\nHTTP:%{http_code}" -X POST "https://api.xiaomimimo.com/v1/chat/completions" \
  -H "api-key: $KEY" \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"mimo-v2.5-tts\",
    \"messages\": [
      {\"role\": \"user\", \"content\": \"用自然亲切的语气播报\"},
      {\"role\": \"assistant\", \"content\": \"$TEXT\"}
    ],
    \"audio\": {\"format\": \"wav\", \"voice\": \"$VOICE\"},
    \"stream\": false
  }")

HTTP_CODE=$(echo "$RESP" | tail -1 | sed 's/HTTP://')
BODY=$(echo "$RESP" | sed '$d')

echo "HTTP 状态码: $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo "✅ API 连通成功"
  echo ""
  
  HAS_AUDIO=$(echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print('yes' if d.get('choices',[{}])[0].get('message',{}).get('audio',{}).get('data') else 'no')" 2>/dev/null)
  
  if [ "$HAS_AUDIO" = "yes" ]; then
    echo "✅ 响应含 Base64 音频数据"
    echo ""
    echo "提取音频..."
    echo "$BODY" | python3 -c "
import sys,json,base64
d = json.load(sys.stdin)
b64 = d['choices'][0]['message']['audio']['data']
with open('/tmp/mimo-test.wav', 'wb') as f:
    f.write(base64.b64decode(b64))
print('✅ 已保存: /tmp/mimo-test.wav')
" && file /tmp/mimo-test.wav && afplay /tmp/mimo-test.wav
  else
    echo "⚠️  响应结构异常，打印前 500 字符:"
    echo "$BODY" | head -c 500
  fi
elif [ "$HTTP_CODE" = "401" ]; then
  echo "❌ 401 - API Key 无效，请替换脚本中的 YOUR_MIMO_KEY"
elif [ "$HTTP_CODE" = "400" ]; then
  echo "❌ 400 - 请求参数错误"
  echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
else
  echo "❌ HTTP $HTTP_CODE"
  echo "$BODY" | head -c 500
fi
