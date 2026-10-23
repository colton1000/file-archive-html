#!/usr/bin/env python3
"""FrameForge LAN project server. Uses only Python's standard library."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, unquote
import argparse, json, os, re, socket, threading, time, uuid, webbrowser

ROOT = Path(__file__).resolve().parent
PROJECTS = ROOT / "frameforge_online_projects"
MAX_UPLOAD = 100 * 1024 * 1024
HTML_HINT = "frameforge_online_market_mvp_luck"


def find_html(directory: Path | None = None) -> Path:
    """Return the preferred FrameForge HTML file from a directory."""
    root = (directory or ROOT).resolve()
    files = sorted(root.glob("*.html"), key=lambda p: p.name.lower())
    if not files:
        raise SystemExit(f"No HTML file found in {root}")

    preferred = [p for p in files if HTML_HINT in p.stem.lower()]
    if not preferred:
        preferred = [p for p in files if "frameforge" in p.stem.lower()]
    return preferred[0] if preferred else files[0]


def safe_title(value):
    value = re.sub(r"[\x00-\x1f<>:\"/\\|?*]+", " ", str(value or "Untitled Project"))
    value = re.sub(r"\s+", " ", value).strip()
    return value[:80] or "Untitled Project"


def project_summary(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "id": path.stem,
            "name": safe_title(data.get("name")),
            "updatedAt": data.get("updatedAt") or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(path.stat().st_mtime)),
            "frames": len(data.get("frames", [])),
            "size": path.stat().st_size,
        }
    except Exception:
        return None


class Handler(SimpleHTTPRequestHandler):
    server_version = "FrameForgeServer/1.0"

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "same-origin")
        super().end_headers()

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))

    def send_json(self, code, value):
        raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.send_response(302)
            self.send_header("Location", "/" + self.server.html_file.name)
            self.end_headers()
            return
        if parsed.path == "/api/status":
            self.send_json(200, {"ok": True, "app": "FrameForge", "uploads": True})
            return
        if parsed.path == "/api/projects":
            items = [x for x in (project_summary(p) for p in PROJECTS.glob("*.json")) if x]
            items.sort(key=lambda x: x["updatedAt"], reverse=True)
            self.send_json(200, {"projects": items})
            return
        if parsed.path.startswith("/api/projects/"):
            project_id = unquote(parsed.path.rsplit("/", 1)[-1])
            if not re.fullmatch(r"[a-f0-9-]{8,64}", project_id):
                self.send_json(400, {"error": "Invalid project ID"}); return
            path = PROJECTS / (project_id + ".json")
            if not path.exists():
                self.send_json(404, {"error": "Project not found"}); return
            try:
                self.send_json(200, json.loads(path.read_text(encoding="utf-8")))
            except Exception:
                self.send_json(500, {"error": "Stored project is damaged"})
            return
        super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/api/projects":
            self.send_json(404, {"error": "Not found"}); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length <= 0:
            self.send_json(400, {"error": "Project upload was empty"}); return
        if length > MAX_UPLOAD:
            self.send_json(413, {"error": "Project exceeds the 100 MiB server upload limit"}); return
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except Exception:
            self.send_json(400, {"error": "Upload is not valid JSON"}); return
        if not isinstance(data, dict) or data.get("app") != "FrameForge":
            self.send_json(400, {"error": "This is not a FrameForge project"}); return
        frames = data.get("frames")
        if not isinstance(frames, list) or not frames:
            self.send_json(400, {"error": "Project has no frames"}); return
        if len(frames) > 5000:
            self.send_json(400, {"error": "Project has too many frames"}); return
        data["name"] = safe_title(data.get("name"))
        data["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        project_id = uuid.uuid4().hex
        temp = PROJECTS / (project_id + ".tmp")
        final = PROJECTS / (project_id + ".json")
        temp.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        os.replace(temp, final)
        self.send_json(201, {
            "ok": True,
            "project": project_summary(final),
            "openUrl": f"/api/projects/{project_id}",
        })


def local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80)); return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def main():
    ap = argparse.ArgumentParser(description="Host FrameForge and its shared project library")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    PROJECTS.mkdir(exist_ok=True)
    html = find_html()
    os.chdir(ROOT)
    server = ThreadingHTTPServer(("0.0.0.0", args.port), Handler)
    server.html_file = html
    url = f"http://127.0.0.1:{args.port}/"
    print(f"\nFrameForge is running: {url}")
    print(f"Other devices on this network: http://{local_ip()}:{args.port}/")
    print(f"Using HTML: {html.name}")
    print("Press Ctrl+C to stop.\n")
    if not args.no_browser:
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping FrameForge server...")
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
