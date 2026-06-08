from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx

from src.core.config_manager import ProxyConfig
from src.services.codex_proxy_server import CodexProxyServer


class CodexProxyServerTests(unittest.TestCase):
    def test_random_port_proxy_converts_request_and_response(self) -> None:
        captured = {}

        class UpstreamHandler(BaseHTTPRequestHandler):
            def log_message(self, _format, *_args):
                return

            def do_POST(self):
                length = int(self.headers["Content-Length"])
                captured["body"] = json.loads(self.rfile.read(length))
                response = {
                    "id": "chat_1",
                    "model": "deepseek-v4-pro",
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": "pong",
                            }
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 2,
                    },
                }
                data = json.dumps(response).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

        upstream = ThreadingHTTPServer(("127.0.0.1", 0), UpstreamHandler)
        thread = threading.Thread(target=upstream.serve_forever, daemon=True)
        thread.start()
        logs = []
        router = CodexProxyServer(
            upstream_base_url=f"http://127.0.0.1:{upstream.server_address[1]}",
            api_key="test-key",
            model="deepseek-v4-pro",
            proxy=ProxyConfig(),
            log=logs.append,
        )
        router.start()
        try:
            self.assertGreater(router.port, 0)
            with httpx.Client(trust_env=False) as client:
                response = client.post(
                    f"{router.base_url}/responses",
                    json={
                        "model": "client-model",
                        "input": "ping",
                        "stream": False,
                    },
                    timeout=5,
                )
            self.assertEqual(
                response.status_code,
                200,
                f"{response.text}\nlogs={logs}",
            )
            self.assertEqual(
                captured["body"]["model"],
                "deepseek-v4-pro",
            )
            self.assertEqual(
                response.json()["output"][0]["content"][0]["text"],
                "pong",
            )
        finally:
            router.stop()
            upstream.shutdown()
            upstream.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
