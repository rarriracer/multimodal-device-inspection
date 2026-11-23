"""Loopback-only portfolio demo. Inputs stay in memory; no external APIs."""
from __future__ import annotations

import argparse
import base64
from functools import lru_cache
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
import importlib.util
import json
import mimetypes
from pathlib import Path
import sys
import threading
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from device_inspection.text import TextModel

VISION_LOCK = threading.Lock()


@lru_cache(maxsize=1)
def text_model():
    return TextModel(ROOT / "models/text_baseline.json")


@lru_cache(maxsize=1)
def view_model():
    from device_inspection.vision import ViewModel
    return ViewModel(ROOT / "models/device_views.npz")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def respond(self, status, data, content_type="application/json"):
        body = json.dumps(data).encode() if content_type == "application/json" else data
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' blob: data:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/examples":
            return self.respond(200, json.loads((ROOT / "examples/cases.json").read_text()))
        if path == "/api/status":
            return self.respond(200, {"text": True, "vision": all(importlib.util.find_spec(name) is not None
                for name in ("torch", "torchvision")) and (ROOT / "models/device_views.npz").is_file()})
        target = ROOT / "app/index.html" if path == "/" else ROOT / path.lstrip("/")
        target = target.resolve()
        allowed = any(target.is_relative_to(ROOT / folder) for folder in ("app", "examples/images"))
        if not allowed or not target.is_file() or target.suffix not in (".html", ".css", ".js", ".svg", ".png"):
            return self.respond(404, {"error": "Not found"})
        return self.respond(200, target.read_bytes(), mimetypes.guess_type(target)[0] or "application/octet-stream")

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + self.headers.get("Host", ""):
            return self.respond(403, {"error": "Cross-origin requests are disabled"})
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if not 0 < size <= 12_000_000:
                return self.respond(413, {"error": "Request must be between 1 byte and 12 MB"})
            data = json.loads(self.rfile.read(size))
            path = urlparse(self.path).path
            if path == "/api/text":
                return self.respond(200, text_model().predict(data["text"]))
            if path == "/api/vision":
                if not isinstance(data.get("image"), str):
                    raise ValueError("An encoded local image is required")
                from PIL import Image, ImageOps
                with Image.open(BytesIO(base64.b64decode(data["image"], validate=True))) as source:
                    if source.width * source.height > 20_000_000:
                        raise ValueError("Image exceeds 20 megapixels")
                    image = ImageOps.exif_transpose(source).convert("RGB")
                with VISION_LOCK:
                    return self.respond(200, view_model().predict(image))
            return self.respond(404, {"error": "Not found"})
        except (ValueError, KeyError, TypeError, OSError) as exc:
            return self.respond(400, {"error": str(exc)[:180]})
        except ImportError:
            return self.respond(503, {"error": "Install the vision extra to run local image inference."})
        except Exception:
            return self.respond(500, {"error": "Model could not process this input."})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Inspection workspace: http://127.0.0.1:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
