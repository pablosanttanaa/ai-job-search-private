#!/usr/bin/env python3
"""Unattended job scrape for the dashboard button and the daily 13:00 timer.

`/scrape` is a Claude skill, so it cannot run on a headless server by itself.
This script runs the same portal CLIs (linkedin-search, freehire-search) with
the queries from .claude/skills/job-scraper/search-queries.md, scores each new
posting with transparent rules derived from the candidate profile, and merges
the result into job_scraper/seen_jobs.json using the same schema and the same
key helper (tools/job_key.py) as `/scrape`. Existing entries are never touched,
so `/rank` and `/apply` keep working on the same file.

The score is a heuristic triage signal (`auto_score`), not the full fit
evaluation - `/rank` remains the place for that.

Usage:
    python3 tools/daily_scrape.py [--trigger manual|timer] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from job_key import make_key  # noqa: E402
from job_rules import (  # noqa: E402
    CANARIAS, OFF_TARGET, RELEVANT, SENIOR, base_score, evaluate, extract_facts, matched_keyword, norm,
)
from job_settings import load as load_settings  # noqa: E402

STATE = ROOT / "job_scraper" / "seen_jobs.json"
RUNS = ROOT / "job_scraper" / "runs.json"
LOCK = ROOT / "job_scraper" / "scrape.lock"
SKILLS = ROOT / ".agents" / "skills"
LINKEDIN = SKILLS / "linkedin-search" / "cli" / "src" / "cli.ts"
FREEHIRE = SKILLS / "freehire-search" / "cli" / "src" / "cli.ts"

WINDOW_DAYS = 14
MAX_DETAILS = 25          # LinkedIn detail fetches per run (keep volume low - ToS)
LINKEDIN_PAUSE = 3        # seconds between LinkedIn calls
LOCK_STALE = 3600         # a lock older than this is a crashed run
DESC_MAX = 8000           # description kept for the ATS CV keywords (not sent to the page)


def build_queries(cfg: dict) -> list[tuple[str, str, list[str]]]:
    """(portal, label, args) - translated from search-queries.md priorities 1-3.

    Remote-only queries are dropped when teletrabajo is not wanted, queries
    for portals left out of the settings are dropped, and the local LinkedIn
    query follows the first configured location.
    """
    remote = "remoto" in cfg["work_modes"]
    queries = [
        ("linkedin-search", "Odoo", ["-q", "Odoo", "-l", "Spain", "--jobage", "14"]),
        ("linkedin-search", "desarrollador Odoo", ["-q", "desarrollador Odoo", "-l", "Spain", "--jobage", "14"]),
        ("linkedin-search", "programador Odoo", ["-q", "programador Odoo", "-l", "Spain", "--jobage", "14"]),
        ("linkedin-search", "Odoo developer", ["-q", "Odoo developer", "-l", "Spain", "--jobage", "14"]),
        ("linkedin-search", "consultor Odoo", ["-q", "consultor Odoo", "-l", "Spain", "--jobage", "14"]),
        ("linkedin-search", "Odoo remoto", ["-q", "Odoo", "-l", "Spain", "--remote", "remote", "--jobage", "14"]) if remote else None,
        ("linkedin-search", "ERP Python", ["-q", "ERP Python PostgreSQL", "-l", "Spain", "--jobage", "14"]),
        ("linkedin-search", "desarrollador Python", ["-q", "desarrollador Python", "-l", "Spain", "--jobage", "14"]),
        ("freehire-search", "odoo ES", ["-q", "odoo", "--country", "ES", "--jobage", "14", "-n", "20"]),
        ("freehire-search", "odoo remoto EU", ["-q", "odoo", "--remote", "remote", "--region", "eu,none", "--jobage", "14", "-n", "20"]) if remote else None,
        ("freehire-search", "erp python ES", ["-q", "erp python", "--country", "ES", "--jobage", "14", "-n", "15"]),
    ]
    if cfg["locations"]:
        first = cfg["locations"][0]
        where = "Canary Islands, Spain" if CANARIAS.search(first) else f"{first}, Spain"
        queries.insert(8, ("linkedin-search", first, ["-q", "desarrollador", "-l", where, "--jobage", "14"]))
    return [q for q in queries if q and q[0] in cfg["portals"]]

# --- scoring --------------------------------------------------------------

def score(title: str, desc: str, location: str, today: date, cfg: dict) -> tuple[dict, int, dict]:
    """Return (facts, base score, evaluation) for one posting - see tools/job_rules.py."""
    facts = extract_facts(title, desc)
    base = base_score(title, desc)
    probe = {"title": title, "description": desc, "location": location, "facts": facts, "base_score": base}
    return facts, base, evaluate(probe, cfg, today)


# --- portal CLIs ----------------------------------------------------------

def bun_path() -> str:
    found = os.environ.get("BUN") or shutil.which("bun")
    if found:
        return found
    home = Path.home() / ".bun" / "bin" / ("bun.exe" if os.name == "nt" else "bun")
    if home.exists():
        return str(home)
    raise SystemExit("bun no encontrado (instálalo o define BUN=/ruta/a/bun)")


def run_cli(bun: str, cli: Path, args: list[str], timeout: int = 120) -> dict:
    proc = subprocess.run([bun, "run", str(cli), *args, "--format", "json"],
                          capture_output=True, text=True, encoding="utf-8", timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout).strip()[:300] or f"exit {proc.returncode}")
    return json.loads(proc.stdout)


# --- state ----------------------------------------------------------------

def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def acquire_lock() -> bool:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    if LOCK.exists() and time.time() - LOCK.stat().st_mtime > LOCK_STALE:
        LOCK.unlink(missing_ok=True)
    try:
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    os.write(fd, f"{os.getpid()} {datetime.now().isoformat(timespec='seconds')}".encode())
    os.close(fd)
    return True


def today_madrid() -> date:
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Madrid")).date()
    except Exception:
        return date.today()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--trigger", default="manual", choices=["manual", "timer"])
    ap.add_argument("--dry-run", action="store_true", help="search and score, write nothing")
    args = ap.parse_args()

    if not acquire_lock():
        print("Ya hay una búsqueda en marcha; salgo.")
        return 2

    started = datetime.now().astimezone().isoformat(timespec="seconds")
    today = today_madrid()
    cutoff = today - timedelta(days=WINDOW_DAYS)
    errors: list[str] = []
    added: list[dict] = []
    try:
        cfg = load_settings()
        bun = bun_path()
        state = load_json(STATE, {"seen": {}})
        seen = state.setdefault("seen", {})
        known_urls = {v.get("url") for v in seen.values()}

        pool: dict[str, tuple[dict, str]] = {}
        for i, (portal, label, qargs) in enumerate(build_queries(cfg)):
            cli = LINKEDIN if portal == "linkedin-search" else FREEHIRE
            try:
                if portal == "linkedin-search" and i:
                    time.sleep(LINKEDIN_PAUSE)
                results = run_cli(bun, cli, ["search", *qargs]).get("results", [])
                print(f"[{portal}] {label}: {len(results)}")
            except Exception as exc:  # one failing query never aborts the run
                errors.append(f"{portal} «{label}»: {exc}")
                print(f"[{portal}] {label}: ERROR {exc}")
                continue
            for r in results:
                d = r.get("date")
                if d and date.fromisoformat(d) < cutoff:
                    continue
                pool.setdefault(r.get("url") or r["id"], (r, portal))

        details = 0
        for url, (r, portal) in pool.items():
            title = norm(r.get("title") or "")
            company = norm(r.get("company") or "") or "unknown"
            key = make_key(company, title, url)
            if url in known_urls or key in seen:
                continue
            location = norm(r.get("location") or "")
            desc = norm(r.get("description") or "")
            status = "new"
            facts: dict | None = None
            base = None
            flags: list[str] = []
            s, fit, out = 0, "low", True
            excluded = matched_keyword(title, cfg["exclude_keywords"])
            rules = cfg["rules"]
            if OFF_TARGET.search(title) or not RELEVANT.search(title):
                flags, status = ["fuera de perfil"], "skipped"
            else:
                # A title a hard rule already discards does not spend a LinkedIn
                # detail fetch; it is still stored, so relaxing the rule shows it.
                title_out = (excluded and rules["exclude"] == "hard") or (SENIOR.search(title) and rules["senior"] == "hard")
                if portal == "linkedin-search" and not title_out:
                    if details < MAX_DETAILS:
                        try:
                            time.sleep(LINKEDIN_PAUSE)
                            det = run_cli(bun, LINKEDIN, ["detail", str(r["id"])], timeout=90)
                            details += 1
                            desc = norm(det.get("description") or "")
                            if det.get("isActive") is False:
                                status = "expired"
                        except Exception as exc:
                            errors.append(f"detail {r['id']}: {exc}")
                    else:
                        errors.append(f"detail {r['id']}: tope de {MAX_DETAILS} alcanzado")
                facts, base, ev = score(title, desc, location, today, cfg)
                s, fit, flags, out = ev["score"], ev["fit"], ev["flags"], bool(ev["excluded"])
                if not desc:
                    flags.append("sin descripción")
            sal = facts.get("salary") if facts else None
            entry = {
                "title": title,
                "company": company,
                "url": url,
                "first_seen": today.isoformat(),
                "found_in_run": started,   # = runs.json "started"; marks "new since last run"
                "posted_date": r.get("date"),
                "deadline": None,
                "fit": fit,
                "status": status,
                "portal": portal,
                "source": "cli",
                "location": location or None,
                # auto_* = evaluation with the settings at scrape time; the
                # dashboard re-evaluates base_score + facts with current ones.
                "auto_score": s,
                "auto_flags": flags,
                "base_score": base,
                "facts": facts,
                "work_mode": facts.get("work_mode") if facts else None,
                "salary_min": sal[0] if sal else None,
                "salary_max": sal[1] if sal else None,
                "snippet": re.sub(r"\s+", " ", desc)[:600] or None,
                "description": desc[:DESC_MAX] or None,
            }
            seen[key] = entry
            known_urls.add(url)
            added.append((entry, out))

        if not args.dry_run:
            write_json(STATE, state)
        ok = True
    except Exception as exc:
        errors.append(f"fatal: {exc}")
        ok = False
    finally:
        LOCK.unlink(missing_ok=True)

    # Counted like the dashboard shows them: open and meeting the settings.
    shown = [e for e, out in added if e["status"] == "new" and not out]
    run = {
        "started": started,
        "finished": datetime.now().astimezone().isoformat(timespec="seconds"),
        "trigger": args.trigger,
        "ok": ok,
        "added": len(added),
        "new": len(shown),
        "high": sum(e["fit"] == "high" for e in shown),
        "medium": sum(e["fit"] == "medium" for e in shown),
        "errors": errors[:20],
    }
    if not args.dry_run:
        runs = load_json(RUNS, [])
        runs.append(run)
        write_json(RUNS, runs[-60:])
    print(json.dumps(run, ensure_ascii=False, indent=2))
    for e in sorted(shown, key=lambda e: -e["auto_score"]):
        print(f"  {e['auto_score']:3d} {e['fit']:6s} {e['title']} · {e['company']} · {', '.join(e['auto_flags'])}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
