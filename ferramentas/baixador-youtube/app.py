#!/usr/bin/env python3
"""Baixador de trechos do YouTube.

Servidor local (só biblioteca padrão + yt-dlp + ffmpeg).
Uso:  python3 app.py   ->  abre http://localhost:8765
"""
import json
import os
import re
import subprocess
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, urlparse

BASE = Path(__file__).parent
DOWNLOADS = BASE / "downloads"
DOWNLOADS.mkdir(exist_ok=True)
PORT = 8765
YT_RE = re.compile(r"^https?://(www\.|m\.|music\.)?(youtube\.com|youtu\.be)/", re.I)
JOBS: dict[str, dict] = {}


def ytdlp(*args):
    extra = []
    browser = os.environ.get("YT_COOKIES_BROWSER")  # ex.: chrome, firefox, edge
    if browser:
        extra = ["--cookies-from-browser", browser]
    return [sys.executable, "-m", "yt_dlp", "--no-playlist", "--no-warnings", *extra, *args]


def fmt_time(s: float) -> str:
    s = int(s)
    return f"{s // 3600:d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def get_info(url: str) -> dict:
    out = subprocess.run(ytdlp("-J", url), capture_output=True, text=True, timeout=60)
    if out.returncode:
        raise RuntimeError(out.stderr.strip().splitlines()[-1] if out.stderr else "Falha ao ler o vídeo")
    d = json.loads(out.stdout)
    return {
        "id": d["id"],
        "title": d.get("title", ""),
        "duration": d.get("duration") or 0,
        "thumbnail": d.get("thumbnail", ""),
        "channel": d.get("uploader", ""),
    }


def run_job(job_id: str, url: str, start: float, end: float, kind: str, quality: str):
    job = JOBS[job_id]
    out_dir = DOWNLOADS / job_id
    out_dir.mkdir()
    args = [
        "--download-sections", f"*{fmt_time(start)}-{fmt_time(end)}",
        "--force-keyframes-at-cuts", "--newline",
        "-o", str(out_dir / "%(title).80s [%(id)s] %(section_start)d-%(section_end)d.%(ext)s"),
    ]
    if kind == "audio":
        args += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
    else:
        h = "" if quality == "best" else f"[height<={int(quality)}]"
        args += ["-f", f"bv*{h}+ba/b{h}", "--merge-output-format", "mp4"]
    try:
        p = subprocess.Popen(ytdlp(*args, url), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            m = re.search(r"(\d+(?:\.\d+)?)%", line)
            if m:
                job["progress"] = float(m.group(1))
            job["log"] = line.strip()[-200:]
        p.wait()
        files = [f for f in out_dir.iterdir() if f.is_file() and f.suffix in (".mp4", ".mp3")]
        if p.returncode or not files:
            raise RuntimeError(job.get("log") or "Falha no download")
        job.update(status="done", progress=100, file=f"{job_id}/{files[0].name}", name=files[0].name)
    except Exception as e:  # noqa: BLE001
        job.update(status="error", error=str(e))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send_json(self, obj, code=200):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/":
            body = (BASE / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif u.path == "/api/info":
            url = q.get("url", [""])[0]
            if not YT_RE.match(url):
                return self.send_json({"error": "Cole um link válido do YouTube."}, 400)
            try:
                self.send_json(get_info(url))
            except Exception as e:  # noqa: BLE001
                self.send_json({"error": str(e)}, 400)
        elif u.path == "/api/status":
            job = JOBS.get(q.get("id", [""])[0])
            self.send_json(job or {"status": "error", "error": "Tarefa não encontrada"})
        elif u.path.startswith("/files/"):
            rel = u.path[len("/files/"):]
            f = (DOWNLOADS / rel).resolve()
            if DOWNLOADS.resolve() not in f.parents or not f.is_file():
                return self.send_error(404)
            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg" if f.suffix == ".mp3" else "video/mp4")
            self.send_header("Content-Length", str(f.stat().st_size))
            self.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{quote(f.name)}")
            self.end_headers()
            with open(f, "rb") as fh:
                while chunk := fh.read(1 << 20):
                    self.wfile.write(chunk)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/api/download":
            return self.send_error(404)
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        url = data.get("url", "")
        try:
            start, end = float(data["start"]), float(data["end"])
        except (KeyError, ValueError):
            return self.send_json({"error": "Início/fim inválidos."}, 400)
        if not YT_RE.match(url) or start < 0 or end <= start:
            return self.send_json({"error": "Dados inválidos (o fim deve ser maior que o início)."}, 400)
        kind = "audio" if data.get("kind") == "audio" else "video"
        quality = str(data.get("quality", "best"))
        if quality != "best" and not quality.isdigit():
            quality = "best"
        job_id = uuid.uuid4().hex[:10]
        JOBS[job_id] = {"status": "running", "progress": 0}
        threading.Thread(target=run_job, args=(job_id, url, start, end, kind, quality), daemon=True).start()
        self.send_json({"id": job_id})


if __name__ == "__main__":
    print(f"Baixador de trechos rodando em http://localhost:{PORT}  (Ctrl+C para sair)")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
