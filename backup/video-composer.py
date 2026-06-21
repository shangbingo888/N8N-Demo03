#!/usr/bin/env python3
"""
轻量级视频合成服务
接受 n8n HTTP Request 节点的调用，支持两种模式：
1. /compose: 提供 audio_base64 → 直接解码音频 + 下载图片 + FFmpeg
2. /compose-with-tts: 提供 narration_text → 先调用 Mimo TTS API → FFmpeg
"""

import http.server
import json
import base64
import subprocess
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

# 配置
PORT = int(os.environ.get("COMPOSER_PORT", 8899))
OUTPUT_DIR = os.environ.get("COMPOSER_OUTPUT_DIR", os.path.join(os.path.dirname(__file__), "..", "n8n-files"))
MIMO_API_KEY = os.environ.get("MIMO_API_KEY", "")
MIMO_API_URL = "https://api.xiaomimimo.com/v1/chat/completions"


def call_mimo_tts(text, voice="冰糖", format_type="mp3"):
    """调用 Mimo TTS API 生成音频，返回 base64 编码的音频数据"""
    if not MIMO_API_KEY:
        raise Exception("MIMO_API_KEY 未配置")

    payload = {
        "model": "mimo-v2.5-tts",
        "messages": [
            {"role": "user", "content": "用自然亲切的语气播报，语速适中，富有感染力"},
            {"role": "assistant", "content": text}
        ],
        "audio": {"format": format_type, "voice": voice},
        "stream": False
    }

    req = urllib.request.Request(
        MIMO_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-key": MIMO_API_KEY,
            "Content-Type": "application/json"
        }
    )

    print(f"[Composer] 调用 Mimo TTS (文本长度: {len(text)})...", flush=True)
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    choice = result.get("choices", [{}])[0]
    audio_data = choice.get("message", {}).get("audio", {})
    audio_b64 = audio_data.get("data")
    audio_format = audio_data.get("format", format_type)

    if not audio_b64:
        raise Exception(f"Mimo TTS 未返回音频: {json.dumps(result, ensure_ascii=False)[:300]}")

    print(f"[Composer] TTS 成功 (格式: {audio_format}, base64: {len(audio_b64)} chars)", flush=True)
    return audio_b64, audio_format


class VideoComposerHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[Composer] {args[0]}", flush=True)

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "ok",
                "ffmpeg": bool(subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0),
                "mimo_key": bool(MIMO_API_KEY)
            }).encode())
        elif self.path.startswith("/files/"):
            # 提供视频文件下载
            file_name = self.path[len("/files/"):]
            file_path = os.path.join(OUTPUT_DIR, file_name)
            if not os.path.abspath(file_path).startswith(os.path.abspath(OUTPUT_DIR)):
                self.send_response(403)
                self.end_headers()
                return
            if os.path.isfile(file_path):
                self.send_response(200)
                ext = os.path.splitext(file_name)[1].lower()
                content_types = {".mp4": "video/mp4", ".mp3": "audio/mpeg", ".wav": "audio/wav", ".png": "image/png"}
                self.send_header("Content-Type", content_types.get(ext, "application/octet-stream"))
                self.send_header("Content-Length", str(os.path.getsize(file_path)))
                self.send_header("Content-Disposition", f'inline; filename="{file_name}"')
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_compose(self, data):
        """处理 /compose 请求：audio_base64 模式"""
        image_url = data.get("image_url")
        audio_b64 = data.get("audio_base64")
        fmt = data.get("format", "mp3")
        output_name = data.get("output_name", f"video_{int(__import__('time').time() * 1000)}.mp4")

        if not image_url:
            self._send_error(400, "缺少 image_url")
            return
        if not audio_b64:
            self._send_error(400, "缺少 audio_base64")
            return

        audio_bytes = base64.b64decode(audio_b64)
        self._compose_video(image_url, audio_bytes, fmt, output_name)

    def _handle_compose_with_tts(self, data):
        """处理 /compose-with-tts 请求：先 TTS 再合成"""
        image_url = data.get("image_url")
        narration = data.get("narration")
        voice = data.get("voice", "冰糖")
        fmt = data.get("format", "mp3")
        output_name = data.get("output_name", f"video_{int(__import__('time').time() * 1000)}.mp4")

        if not image_url:
            self._send_error(400, "缺少 image_url")
            return
        if not narration:
            self._send_error(400, "缺少 narration (配音文本)")
            return

        # 调用 Mimo TTS
        try:
            audio_b64, actual_format = call_mimo_tts(narration, voice, fmt)
        except Exception as e:
            self._send_error(500, f"TTS 失败: {str(e)}")
            return

        # 解码音频
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            self._send_error(500, f"音频解码失败: {str(e)}")
            return

        self._compose_video(image_url, audio_bytes, actual_format or fmt, output_name)

    def _compose_video(self, image_url, audio_bytes, format_type, output_name):
        """下载/复制图片 + 写入音频 + FFmpeg 合成"""
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                image_path = os.path.join(tmpdir, "scene.png")
                audio_path = os.path.join(tmpdir, f"audio.{format_type}")
                output_path = os.path.join(OUTPUT_DIR, output_name)

                Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

                # 获取图片：本地文件直接使用，HTTP URL 则下载
                if image_url.startswith("http://") or image_url.startswith("https://"):
                    print(f"[Composer] 下载图片: {image_url[:80]}...", flush=True)
                    urllib.request.urlretrieve(image_url, image_path)
                elif os.path.isfile(image_url):
                    print(f"[Composer] 使用本地图片: {image_url}", flush=True)
                    image_path = image_url  # 直接使用共享卷中的文件
                else:
                    self._send_error(400, f"图片不可访问: {image_url}")
                    return

                # 写入音频
                print(f"[Composer] 写入音频 ({len(audio_bytes)} bytes)...", flush=True)
                with open(audio_path, "wb") as f:
                    f.write(audio_bytes)

                # FFmpeg
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1", "-i", image_path,
                    "-i", audio_path,
                    "-c:v", "libx264", "-tune", "stillimage",
                    "-c:a", "aac", "-b:a", "192k",
                    "-pix_fmt", "yuv420p",
                    "-shortest",
                    output_path
                ]
                print(f"[Composer] FFmpeg: {' '.join(cmd)}", flush=True)
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

                if result.returncode == 0:
                    file_size = os.path.getsize(output_path)
                    print(f"[Composer] ✅ 视频就绪: {output_path} ({file_size} bytes)", flush=True)
                    self._send_success(output_name, file_size)
                else:
                    err = result.stderr[-500:] if result.stderr else "unknown"
                    print(f"[Composer] ❌ FFmpeg 失败: {err}", flush=True)
                    self._send_error(500, f"FFmpeg 失败: {err}")

        except subprocess.TimeoutExpired:
            self._send_error(500, "FFmpeg 执行超时 (120s)")
        except Exception as e:
            print(f"[Composer] 异常: {str(e)}", flush=True)
            self._send_error(500, f"合成异常: {str(e)}")

    def do_POST(self):
        if self.path == "/compose":
            self._handle_request(self._handle_compose)
        elif self.path == "/compose-with-tts":
            self._handle_request(self._handle_compose_with_tts)
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_request(self, handler):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            data = json.loads(body)
            handler(data)
        except json.JSONDecodeError:
            self._send_error(400, "无效的 JSON 请求体")
        except Exception as e:
            print(f"[Composer] 未处理异常: {str(e)}", flush=True)
            self._send_error(500, f"内部错误: {str(e)}")

    def _send_success(self, file_name, file_size):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "success": True,
            "fileName": file_name,
            "fileUrl": f"http://localhost:{PORT}/files/{file_name}",
            "fileSize": file_size
        }).encode())

    def _send_error(self, code, message):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "success": False,
            "error": message
        }).encode())


def main():
    print(f"[Composer] 启动视频合成服务: 0.0.0.0:{PORT}", flush=True)
    print(f"[Composer] 输出目录: {OUTPUT_DIR}", flush=True)

    # 确保输出目录存在
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

    server = http.server.HTTPServer(("0.0.0.0", PORT), VideoComposerHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Composer] 服务已停止", flush=True)
        server.shutdown()


if __name__ == "__main__":
    main()
