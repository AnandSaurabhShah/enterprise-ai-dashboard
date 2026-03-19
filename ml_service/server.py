from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from runtime import Runtime, ollama_status


HOST = "127.0.0.1"
PORT = 8790
RUNTIME = Runtime.load()


class Handler(BaseHTTPRequestHandler):
    server_version = "EnterpriseAIModelService/1.0"

    def _send(self, status: int, payload) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8") or "{}")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            ollama_ok, ollama_note = ollama_status()
            self._send(
                200,
                {
                    "ok": True,
                    "service": "enterprise-ai-model-service",
                    "models": sorted(RUNTIME.models.keys()),
                    "llmEnabled": ollama_ok,
                    "llmProvider": ollama_note,
                },
            )
            return
        if path == "/summary":
            self._send(200, RUNTIME.summary())
            return
        self._send(404, {"error": "Not found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path != "/infer":
            self._send(404, {"error": "Not found"})
            return
        try:
            payload = self._read_json()
            result = RUNTIME.infer(
                payload.get("featureId"),
                payload.get("actionId"),
                payload.get("inputs") or {},
                payload.get("session") or {},
            )
            self._send(
                200,
                {
                    "featureId": payload.get("featureId"),
                    "actionId": payload.get("actionId"),
                    "result": result,
                },
            )
        except Exception as error:  # noqa: BLE001
            self._send(400, {"error": str(error)})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Enterprise AI model service listening on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
