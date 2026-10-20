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
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from job_key import make_key  # noqa: E402
from job_settings import MODE_LABEL, load as load_settings  # noqa: E402

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
CANDIDATE_START = date(2025, 2, 1)   # first day at Orbalia (CV)


def build_queries(cfg: dict) -> list[tuple[str, str, list[str]]]:
    """(portal, label, args) - translated from search-queries.md priorities 1-3.

    Remote-only queries are dropped when teletrabajo is not wanted, and the
    local LinkedIn query follows the first configured location.
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
    return [q for q in queries if q]

# --- scoring rules --------------------------------------------------------

OFF_TARGET = re.compile(
    r"\bsap\b|dynamics|business central|salesforce|netsuite|administrativ|contab|contable|"
    r"bookkeep|accountant|n[oó]minas|comercial|account (executive|manager)|sales|partnership|"
    r"\bmmc\b|controller|fiscal|compras|marketing|recursos humanos|\.net\b|\bjava\b|\bphp\b|"
    r"mecatr[oó]nic|auditor|cad\b",
    re.I,
)
RELEVANT = re.compile(
    r"odoo|python|\berp\b|desarrollador|developer|programador|backend|integraci|"
    r"consultor|ingenier|engineer|software|sistemas",
    re.I,
)
SENIOR = re.compile(r"\b(senior|sr\.?|lead|principal|principle|head|manager|jefe|staff|arquitect)", re.I)
DEV_TITLE = re.compile(r"desarrollador|developer|programador|engineer|ingenier|t[eé]cnico.funcional|backend", re.I)
ENGLISH_HIGH = re.compile(
    r"ingl[eé]s\s*(?:\(|:|-)?\s*(?:alto|avanzado|fluido|nativo|biling|c1|c2|b2)|"
    r"nivel\s+(?:alto|avanzado|medio-alto)\s+de\s+(?:espa[nñ]ol\s+e\s+)?ingl|"
    r"b2-c1[^.]{0,30}ingl|ingl[eé]s[^.]{0,20}imprescindible|"
    r"fluent\s+english|english\s+(?:fluency|proficiency)|proficiency\s+in\s+english|"
    r"(?:clear|good|strong|excellent)\s+(?:written\s+and\s+spoken\s+)?english|working\s+english|"
    r"english\s+(?:upper|advanced|c1|b2)",
    re.I,
)
OTHER_LANGS = r"ucraniano|ukrainian|alem[aá]n|german|franc[eé]s|french|portugu[eé]s|portuguese|italiano|italian|polaco|polish|ruso|russian|neerland[eé]s|dutch"
OTHER_LANG_REQUIRED = re.compile(
    rf"(?:proficiency|imprescindible|required|fluent|nivel alto|dominio)[^.]{{0,60}}\b({OTHER_LANGS})\b|"
    rf"\b({OTHER_LANGS})\b[^.]{{0,30}}(?:imprescindible|required|speaker|nativo)",
    re.I,
)
WORD_NUM = {"un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6}
YEARS = re.compile(
    r"(?:m[ií]nimo(?: de)?|al menos|m[aá]s de|at least|minimum(?: of)?)\s+(\d+|\w+)\s*\+?\s*(?:a[nñ]os|years)|"
    r"(\d+)\s*\+\s*(?:a[nñ]os|years)|"
    # "entre 1 y 3 años" / "1-3 years" is a nice-to-have band, not a floor
    r"(?<!y )(?<!and )(?<!-)(?<!- )(?<!a )(?<!to )\b(\d+)\s*(?:a[nñ]os|years)\s+(?:de\s+experiencia|of\s+(?:commercial\s+|professional\s+)?(?:experience|python|odoo))",
    re.I,
)
IN_SPAIN = re.compile(
    r"spain|espa[nñ]a|\bES\b|\bES\d{2,3}\b|remot|europe|canari|madrid|barcelona|valencia|m[aá]laga|sevilla|"
    r"bilbao|alicante|murcia|zaragoza|castell|le[oó]n|vigo|coru|asturias|navarra|pamplona|girona|"
    r"tarragona|lleida|granada|c[aá]diz|baleares|mallorca|vizcaya|getxo|san sebasti|donostia",
    re.I,
)
REMOTE = re.compile(r"100\s*%\s*remot|full(?:y)?\s*remote|modalidad remota|trabajo remoto|teletrabajo total|\bremote\b", re.I)
HYBRID = re.compile(r"h[ií]brid|hybrid|d[ií]as? (?:en|de) (?:oficina|remoto|teletrabajo)", re.I)
CANARIAS = re.compile(r"canari|las palmas|tenerife|gran canaria|lanzarote|fuerteventura", re.I)
SALARY_CONTEXT = re.compile(r"salari|retribu|sueldo|brut|salary|compensation|€|\beur\b|euros", re.I)
AMOUNT = re.compile(r"(\d{2,3})[.,](\d{3})(?!\d)|(\d{2,3})\s?k\b", re.I)


def _norm(text: str) -> str:
    return unicodedata.normalize("NFC", text or "")


def _fold(text: str) -> str:
    """Lower-case and strip accents, for keyword matching."""
    return "".join(c for c in unicodedata.normalize("NFD", text or "") if not unicodedata.combining(c)).lower()


def matched_keyword(text: str, keywords: list[str]) -> str | None:
    folded = _fold(text)
    return next((k for k in keywords if _fold(k) in folded), None)


def work_mode(text: str) -> str:
    """remoto / hibrido / presencial ("presencial" also covers "not stated")."""
    if REMOTE.search(text):
        return "remoto"
    if HYBRID.search(text):
        return "hibrido"
    return "presencial"


def candidate_years(today: date) -> float:
    return (today - CANDIDATE_START).days / 365.25


def required_years(desc: str) -> int | None:
    found = []
    for m in YEARS.finditer(desc):
        raw = next(g for g in m.groups() if g)
        n = int(raw) if raw.isdigit() else WORD_NUM.get(raw.lower())
        if n and n <= 15:
            found.append(n)
    return max(found) if found else None


def salary_range(desc: str) -> tuple[int, int] | None:
    """Yearly amounts quoted in sentences that talk about pay, as (min, max)."""
    amounts = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", desc):
        if not SALARY_CONTEXT.search(sentence):
            continue
        for m in AMOUNT.finditer(sentence):
            value = int(m[1]) * 1000 + int(m[2]) if m[1] else int(m[3]) * 1000
            if 12000 <= value <= 250000:
                amounts.append(value)
    if not amounts:
        return None
    return min(amounts), max(amounts)


def score(title: str, desc: str, location: str, today: date, cfg: dict) -> tuple[int, list[str], str, dict]:
    """Return (0-100 score, flags, fit band, facts) for one posting.

    `facts` holds what the dashboard needs to re-check a posting against
    settings changed after it was scored: work_mode and the quoted salary.
    """
    text = f"{title}\n{desc}"
    floor = cfg["min_salary"]
    floor_k = f"{floor / 1000:g}k"
    flags: list[str] = []
    s = 30
    if re.search(r"odoo", title, re.I):
        s += 30
    elif re.search(r"odoo", desc, re.I):
        s += 15
    if re.search(r"python", text, re.I):
        s += 10
    if re.search(r"postgre", text, re.I):
        s += 5
    if re.search(r"qweb|\bxml\b", text, re.I):
        s += 4
    if re.search(r"\bapi|integraci|xml-rpc|rest\b", text, re.I):
        s += 4
    if re.search(r"\baws\b|linux", text, re.I):
        s += 3
    if DEV_TITLE.search(title):
        s += 8
    if SENIOR.search(title):
        s -= 20
        flags.append("senior")

    need = required_years(desc)
    have = candidate_years(today)
    if need and need > have:
        if need > have + 0.5:
            s -= min(25, round(12 * (need - have)))
        flags.append(f"pide {need}+ años")

    if location and not IN_SPAIN.search(location):
        s -= 20
        flags.append("fuera de España")

    if ENGLISH_HIGH.search(text):
        if cfg["penalize_english"]:
            s -= 15
        flags.append("⚠ inglés alto")
    other = OTHER_LANG_REQUIRED.search(text)
    if other:
        lang = next(g for g in other.groups() if g)
        flags.append(f"⚠ exige {lang.lower()}")

    sal = salary_range(desc)
    if sal:
        lo, hi = sal
        if hi < floor:
            flags.append(f"salario {lo:,}–{hi:,} € < {floor_k}".replace(",", "."))
        elif lo < floor:
            s -= 5
            flags.append(f"salario {lo:,}–{hi:,} € (baja de {floor_k})".replace(",", "."))
        else:
            s += 3
            flags.append(f"salario {lo:,}–{hi:,} €".replace(",", "."))
    else:
        flags.append("salario no indicado")

    mode = work_mode(text)
    local = matched_keyword(f"{location}\n{title}", cfg["locations"])
    if local:
        s += 10
        flags.append(f"en tu zona ({local})")
    if mode == "remoto":
        flags.append("remoto")
        if "remoto" in cfg["work_modes"]:
            s += 8
    elif mode == "hibrido":
        flags.append("híbrido")
    if mode not in cfg["work_modes"]:
        s -= 20
        flags.append(f"modalidad no deseada ({MODE_LABEL[mode]})")
    elif cfg["scope"] == "local" and mode != "remoto" and not local:
        s -= 25
        flags.append("fuera de tu zona")

    s = max(0, min(100, s))
    fit = "high" if s >= 70 else "medium" if s >= 45 else "low"
    below_floor = bool(sal and sal[1] < floor)
    if other or below_floor:
        fit = "low"   # language gate / salary deal-breaker override skill fit
    facts = {"work_mode": mode, "salary": sal, "below_floor": below_floor}
    return s, flags, fit, facts


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

    started = datetime.now().isoformat(timespec="seconds")
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
            title = _norm(r.get("title") or "")
            company = _norm(r.get("company") or "") or "unknown"
            key = make_key(company, title, url)
            if url in known_urls or key in seen:
                continue
            location = _norm(r.get("location") or "")
            desc = _norm(r.get("description") or "")
            status = "new"
            facts: dict = {}
            excluded = matched_keyword(title, cfg["exclude_keywords"])
            if excluded:
                s, flags, fit, status = 0, [f"excluida por «{excluded}»"], "low", "skipped"
            elif OFF_TARGET.search(title) or not RELEVANT.search(title):
                s, flags, fit, status = 0, ["fuera de perfil"], "low", "skipped"
            else:
                if portal == "linkedin-search":
                    if details < MAX_DETAILS:
                        try:
                            time.sleep(LINKEDIN_PAUSE)
                            det = run_cli(bun, LINKEDIN, ["detail", str(r["id"])], timeout=90)
                            details += 1
                            desc = _norm(det.get("description") or "")
                            if det.get("isActive") is False:
                                status = "expired"
                        except Exception as exc:
                            errors.append(f"detail {r['id']}: {exc}")
                    else:
                        errors.append(f"detail {r['id']}: tope de {MAX_DETAILS} alcanzado")
                s, flags, fit, facts = score(title, desc, location, today, cfg)
                if not desc:
                    flags.append("sin descripción")
                if facts["below_floor"]:
                    status = "skipped"
            sal = facts.get("salary")
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
                "auto_score": s,
                "auto_flags": flags,
                "work_mode": facts.get("work_mode"),
                "salary_min": sal[0] if sal else None,
                "salary_max": sal[1] if sal else None,
                "snippet": re.sub(r"\s+", " ", desc)[:600] or None,
            }
            seen[key] = entry
            known_urls.add(url)
            added.append(entry)

        if not args.dry_run:
            write_json(STATE, state)
        ok = True
    except Exception as exc:
        errors.append(f"fatal: {exc}")
        ok = False
    finally:
        LOCK.unlink(missing_ok=True)

    shown = [e for e in added if e["status"] == "new"]
    run = {
        "started": started,
        "finished": datetime.now().isoformat(timespec="seconds"),
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
