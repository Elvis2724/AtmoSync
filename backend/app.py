"""
AtmoSync: Real-Time Supply Chain & Micro-Climate Arbitrage Backend Server
-------------------------------------------------------------------------
Zero-dependency Python HTTP + REST API Server that:
1. Runs the background IoT Telemetry Simulator & ELT Pipeline (`AtmoSyncEngine`)
2. Serves the Executive BI & Trading Dashboard (`../frontend/`)
3. Exposes real-time REST endpoints and serves Star-Schema CSVs & DAX files from `../powerbi db/`.
"""

from __future__ import annotations

import json
import mimetypes
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

from atmosync_engine import AtmoSyncEngine
from config import (
    BACKEND_DIR,
    DATA_SEED_DIR,
    DEFAULT_HOST,
    DEFAULT_PORT,
    FRONTEND_DIR,
    POWERBI_DB_ROOT,
    PROJECT_ROOT,
    STREAM_INTERVAL_SECONDS,
)

engine = AtmoSyncEngine()
engine_lock = threading.Lock()
auto_stream_enabled = True


def background_iot_streamer() -> None:
    """Continuously steps the IoT simulator & updates Power BI CSV snapshots."""
    tick_counter = 0
    while True:
        time.sleep(STREAM_INTERVAL_SECONDS)
        if auto_stream_enabled:
            with engine_lock:
                engine.step_simulation(persist_to_db=True)
                tick_counter += 1
                if tick_counter % 3 == 0:
                    engine.export_powerbi_datasets()


class AtmoSyncRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        pass

    def _send_json(self, data: dict, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, file_path: Path) -> None:
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404, "File not found")
            return
        mime_type, _ = mimetypes.guess_type(str(file_path))
        content = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime_type or "text/plain; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/api/state":
            with engine_lock:
                payload = engine.get_dashboard_payload()
                payload["auto_stream_enabled"] = auto_stream_enabled
            self._send_json(payload)
            return

        if path == "/api/export-powerbi":
            with engine_lock:
                paths = engine.export_powerbi_datasets()
            self._send_json({"status": "ok", "exported_files": paths})
            return

        if path in ("/", "/index.html"):
            self._serve_file(FRONTEND_DIR / "index.html")
            return

        rel = path.lstrip("/")
        candidate_frontend = FRONTEND_DIR / rel
        if candidate_frontend.exists() and candidate_frontend.is_file():
            self._serve_file(candidate_frontend)
            return

        candidate_root = PROJECT_ROOT / rel
        if candidate_root.exists() and candidate_root.is_file():
            self._serve_file(candidate_root)
            return

        self.send_error(404, f"Route {path} not found")

    def do_POST(self) -> None:
        global auto_stream_enabled
        parsed = urlparse(self.path)
        path = parsed.path
        content_len = int(self.headers.get("Content-Length", "0"))
        raw_body = (
            self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        )
        try:
            body = json.loads(raw_body) if raw_body else {}
        except json.JSONDecodeError:
            body = {}

        if path == "/api/step":
            with engine_lock:
                engine.step_simulation(persist_to_db=True)
                engine.export_powerbi_datasets()
                payload = engine.get_dashboard_payload()
                payload["auto_stream_enabled"] = auto_stream_enabled
            self._send_json(payload)
            return

        if path == "/api/toggle-stream":
            auto_stream_enabled = not auto_stream_enabled
            with engine_lock:
                payload = engine.get_dashboard_payload()
                payload["auto_stream_enabled"] = auto_stream_enabled
            self._send_json(payload)
            return

        if path == "/api/inject-anomaly":
            cid = body.get("container_id", "ATMO-1190-WAG")
            anomaly_type = body.get("anomaly_type", "HUMIDITY_TEMP_SPIKE")
            with engine_lock:
                engine.inject_anomaly(cid, anomaly_type)
                engine.export_powerbi_datasets()
                payload = engine.get_dashboard_payload()
                payload["auto_stream_enabled"] = auto_stream_enabled
            self._send_json(payload)
            return

        if path == "/api/reroute":
            cid = body.get("container_id")
            target_market_id = body.get("target_market_id")
            if not cid:
                self._send_json({"error": "container_id is required"}, status=400)
                return
            with engine_lock:
                engine.execute_reroute(cid, target_market_id)
                engine.export_powerbi_datasets()
                payload = engine.get_dashboard_payload()
                payload["auto_stream_enabled"] = auto_stream_enabled
            self._send_json(payload)
            return

        if path == "/api/reset":
            with engine_lock:
                engine.__init__()
                engine.export_powerbi_datasets()
                payload = engine.get_dashboard_payload()
                payload["auto_stream_enabled"] = auto_stream_enabled
            self._send_json(payload)
            return

        self._send_json({"error": f"Unknown endpoint {path}"}, status=404)


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> None:
    with engine_lock:
        engine.export_powerbi_datasets()

    streamer = threading.Thread(target=background_iot_streamer, daemon=True)
    streamer.start()

    server = ThreadingHTTPServer((host, port), AtmoSyncRequestHandler)
    print("============================================================")
    print(" AtmoSync: Micro-Climate Arbitrage Analytics Platform")
    print(f" Backend Server              : {BACKEND_DIR}")
    print(f" Frontend UI                 : {FRONTEND_DIR}")
    print(f" Shared Seed Data            : {DATA_SEED_DIR}")
    print(f" Power BI & DB Folder        : {POWERBI_DB_ROOT}")
    print(f" Live Executive Dashboard    : http://{host}:{port}")
    print("============================================================")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down AtmoSync server...")
        server.server_close()


if __name__ == "__main__":
    run_server()
