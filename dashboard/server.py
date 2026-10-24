#!/usr/bin/env python3
"""Job-search dashboard: serves dashboard/index.html plus a tiny JSON API.

    GET  /            the dashboard page
    GET  /api/data      seen_jobs.json entries (each evaluated against the current
                        settings, see tools/job_rules.py) + run history + settings +
                        whether a run is active
    GET  /api/cv/<key>.pdf  ATS-friendly CV tailored to that posting (tools/ats_cv.py)
    GET  /fonts/<file>.woff2  the page's self-hosted font (dashboard/fonts/)
    GET  /api/settings  search preferences (job_scraper/settings.json, see tools/job_settings.py)
    PUT  /api/settings  validate and save search preferences (400 with a message if invalid)
    POST /api/run       start tools/daily_scrape.py in the background (409 if running)

Standard library only. Binds 127.0.0.1 by default: put it behind a reverse proxy
with authentication (see deploy/Caddyfile.snippet) rather than exposing it
directly - the page shows your profile-derived ranking and the button spends
portal requests.

    DASHBOARD_HOST=127.0.0.1 DASHBOARD_PORT=8095 python3 dashboard/server.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import ats_cv  # noqa: E402
import job_rules  # noqa: E402
import job_settings  # noqa: E402

PAGE = Path(__file__).resolve().parent / "index.html"
FONTS = Path(__file__).resolve().parent / "fonts"
STATE = ROOT / "job_scraper" / "seen_jobs.json"
RUNS = ROOT / "job_scraper" / "runs.json"
LOCK = ROOT / "job_scraper" / "scrape.lock"
LOG = ROOT / "job_scraper" / "last_run.log"
SCRAPER = ROOT / "tools" / "daily_scrape.py"
LOCK_STALE = 3600
MAX_BODY = 16 * 1024
FONT_PATH = re.compile(r"^/fonts/([a-z0-9-]{1,60}\.woff2)$")
CV_PATH = re.compile(r"^/api/cv/([A-Za-z0-9_.-]{1,200})\.pdf$")

_child: subprocess.Popen | None = None


def _read(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def evaluated_jobs() -> list[dict]:
    """seen_jobs.json entries with the live evaluation; descriptions stay server-side."""
    cfg = job_settings.load()
    today = date.today()
    base = ats_cv.load_base()
    seen = _read(STATE, {"seen": {}}).get("seen", {})
    jobs = []
    for k, v in seen.items():
        job = {"key": k, **{f: x for f, x in v.items() if f != "description"}}
        job["eval"] = job_rules.evaluate(v, cfg, today)
        job["keywords"] = {x: y for x, y in ats_cv.analyze(v, base).items() if x != "tags"}
        jobs.append(job)
    return jobs


def running() -> bool:
    if _child is not None and _child.poll() is None:
        return True
    return LOCK.exists() and time.time() - LOCK.stat().st_mtime < LOCK_STALE


class Handler(BaseHTTPRequestHandler):
    server_version = "JobDashboard/1.0"

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, data) -> None:
        self._send(code, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
        elif path == "/api/data":
            self._json(200, {"jobs": evaluated_jobs(), "runs": _read(RUNS, [])[-15:], "running": running(),
                             "settings": job_settings.load(),
                             # older runs.json/found_in_run stamps are naive server-local time
                             "utc_offset_min": round(time.localtime().tm_gmtoff / 60)})
        elif (m := FONT_PATH.match(path)) and (FONTS / m[1]).is_file():
            body = (FONTS / m[1]).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "font/woff2")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.end_headers()
            self.wfile.write(body)
        elif m := CV_PATH.match(path):
            self._cv(m[1])
        elif path == "/api/settings":
            self._json(200, job_settings.load())
        else:
            self._json(404, {"error": "not found"})

    def _cv(self, key: str) -> None:
        job = _read(STATE, {"seen": {}}).get("seen", {}).get(key)
        if job is None:
            return self._json(404, {"error": "oferta no encontrada"})
        base = ats_cv.load_base()
        pdf = ats_cv.to_pdf(ats_cv.build(job, base, date.today()))
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Length", str(len(pdf)))
        self.send_header("Content-Disposition", f'inline; filename="{ats_cv.filename(job, base)}"')
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(pdf)

    def _same_origin(self) -> bool:
        # A custom header forces a CORS preflight, so another site cannot
        # write through the visitor's authenticated browser.
        return self.headers.get("X-Requested-With") == "job-dashboard"

    def do_PUT(self) -> None:  # noqa: N802
        if self.path != "/api/settings":
            return self._json(404, {"error": "not found"})
        if not self._same_origin():
            return self._json(403, {"error": "forbidden"})
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = -1
        if not 0 < length <= MAX_BODY:
            return self._json(400, {"error": "petición no válida"})
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            saved = job_settings.save(data)
        except (UnicodeDecodeError, json.JSONDecodeError):
            return self._json(400, {"error": "JSON no válido"})
        except ValueError as exc:
            return self._json(400, {"error": str(exc)})
        self._json(200, saved)

    def do_POST(self) -> None:  # noqa: N802
        global _child
        if self.path != "/api/run":
            return self._json(404, {"error": "not found"})
        if not self._same_origin():
            return self._json(403, {"error": "forbidden"})
        if running():
            return self._json(409, {"error": "ya hay una búsqueda en marcha"})
        log = LOG.open("w", encoding="utf-8")
        _child = subprocess.Popen(
            [sys.executable, str(SCRAPER), "--trigger", "manual"],
            cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        log.close()
        self._json(202, {"started": True})

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write("%s %s\n" % (self.log_date_time_string(), fmt % args))


def main() -> None:
    host = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    port = int(os.environ.get("DASHBOARD_PORT", "8095"))
    print(f"Dashboard en http://{host}:{port}", flush=True)
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
