"""Posting facts, skill score and the settings rules, shared by scraper and dashboard.

tools/daily_scrape.py extracts the *facts* of a posting once (years asked,
English level, salary, work mode...) and a settings-independent skill score
(`base_score`). The dashboard then calls `evaluate()` on every request, so a
change in job_scraper/settings.json re-filters and re-scores postings that were
found before the change - nothing has to be scraped again.

Each rule in the settings has a hardness level (see job_settings.RULES):
    off   the rule is ignored
    soft  the posting keeps showing, loses points and gets a flag
    hard  the posting is discarded (hidden while "Cumplen mis ajustes" is on)

A fact the posting does not state never trips a rule: a posting that does not
mention years of experience passes "como máximo 2 años" even when hard.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import date

CANDIDATE_START = date(2025, 2, 1)   # first day at Orbalia (CV)

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

MODE_LABEL = {"presencial": "presencial", "hibrido": "semipresencial", "remoto": "teletrabajo"}
PORTAL_LABEL = {"linkedin-search": "LinkedIn", "freehire-search": "freehire"}

# Points a "soft" rule takes off the automatic score.
PENALTY = {
    "senior": 20, "english": 15, "other_lang": 25, "salary_low": 20, "salary_unknown": 5,
    "mode": 20, "zone": 25, "abroad": 20, "require": 20, "exclude": 30, "age": 10,
}
YEAR_PENALTY, YEAR_PENALTY_MAX = 12, 30


def norm(text: str) -> str:
    return unicodedata.normalize("NFC", text or "")


def fold(text: str) -> str:
    """Lower-case and strip accents, for keyword matching."""
    return "".join(c for c in unicodedata.normalize("NFD", text or "") if not unicodedata.combining(c)).lower()


def matched_keyword(text: str, keywords: list[str]) -> str | None:
    folded = fold(text)
    return next((k for k in keywords if fold(k) in folded), None)


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
    for m in YEARS.finditer(desc or ""):
        raw = next(g for g in m.groups() if g)
        n = int(raw) if raw.isdigit() else WORD_NUM.get(raw.lower())
        if n and n <= 15:
            found.append(n)
    return max(found) if found else None


def salary_range(desc: str) -> tuple[int, int] | None:
    """Yearly amounts quoted in sentences that talk about pay, as (min, max)."""
    amounts = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", desc or ""):
        if not SALARY_CONTEXT.search(sentence):
            continue
        for m in AMOUNT.finditer(sentence):
            value = int(m[1]) * 1000 + int(m[2]) if m[1] else int(m[3]) * 1000
            if 12000 <= value <= 250000:
                amounts.append(value)
    if not amounts:
        return None
    return min(amounts), max(amounts)


def other_language(text: str) -> str | None:
    m = OTHER_LANG_REQUIRED.search(text or "")
    return next(g for g in m.groups() if g).lower() if m else None


def base_score(title: str, desc: str) -> int:
    """How well the posting's stack matches the CV, before any setting applies."""
    text = f"{title}\n{desc}"
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
    return max(0, min(100, s))


def extract_facts(title: str, desc: str) -> dict:
    """What a posting states, independent of the candidate's settings."""
    text = f"{title}\n{desc}"
    sal = salary_range(desc)
    return {
        "required_years": required_years(desc),
        "senior": bool(SENIOR.search(title)),
        "english_high": bool(ENGLISH_HIGH.search(text)),
        "other_lang": other_language(text),
        "work_mode": work_mode(text),
        "salary": list(sal) if sal else None,
    }


def facts_of(job: dict) -> dict:
    """Stored facts, or the best reconstruction for postings scraped before they existed."""
    if isinstance(job.get("facts"), dict):
        return job["facts"]
    title = job.get("title") or ""
    desc = job.get("description") or job.get("snippet") or ""
    flags = job.get("auto_flags") or []
    facts = extract_facts(title, desc)
    for f in flags:
        m = re.match(r"pide (\d+)\+ años", f)
        if m:
            facts["required_years"] = max(int(m[1]), facts["required_years"] or 0)
        if "inglés alto" in f:
            facts["english_high"] = True
        m = re.match(r"⚠ exige (.+)", f)
        if m:
            facts["other_lang"] = m[1]
    if job.get("work_mode"):
        facts["work_mode"] = job["work_mode"]
    elif "remoto" in flags:
        facts["work_mode"] = "remoto"
    elif "híbrido" in flags:
        facts["work_mode"] = "hibrido"
    if job.get("salary_max") is not None:
        facts["salary"] = [job.get("salary_min") or job["salary_max"], job["salary_max"]]
    return facts


def _eur(n: int) -> str:
    return f"{n:,}".replace(",", ".") + " €"


def evaluate(job: dict, cfg: dict, today: date) -> dict:
    """Apply the settings to one posting.

    Returns {score, fit, flags, excluded, soft}: `excluded` lists the hard rules
    the posting breaks (empty = it meets the settings), `soft` the ones that only
    cost points, and `flags` every alert to show.
    A posting scored by /rank keeps its rank_score and fit - soft rules then only
    add flags, since /rank already weighed those factors.
    """
    title = job.get("title") or ""
    desc = job.get("description") or job.get("snippet") or ""
    location = job.get("location") or ""
    facts = facts_of(job)
    rules = cfg["rules"]
    flags: list[str] = []
    excluded: list[str] = []
    soft: list[str] = []
    penalty = 0
    bonus = 0

    def hit(rule: str, label: str, points: int) -> None:
        nonlocal penalty
        level = rules[rule]
        if level == "hard":
            excluded.append(label)
            flags.append(label)
        elif level == "soft":
            penalty += points
            soft.append(label)
            flags.append(label)

    need = facts.get("required_years")
    if need and need > cfg["max_years"]:
        over = need - cfg["max_years"]
        hit("years", f"pide {need}+ años (máx. {cfg['max_years']})", min(YEAR_PENALTY_MAX, YEAR_PENALTY * over))
    elif need:
        flags.append(f"pide {need} año{'s' if need > 1 else ''}")

    if facts.get("senior"):
        hit("senior", "senior", PENALTY["senior"])
    if facts.get("english_high"):
        hit("english", "⚠ inglés alto", PENALTY["english"])
    if facts.get("other_lang"):
        hit("other_lang", f"⚠ exige {facts['other_lang']}", PENALTY["other_lang"])

    sal = facts.get("salary")
    floor = cfg["min_salary"]
    if sal:
        lo, hi = sal
        rng = f"salario {lo:,}–{hi:,} €".replace(",", ".")
        if hi < floor:
            hit("salary", f"{rng} < {_eur(floor)}", PENALTY["salary_low"])
        elif lo < floor:
            flags.append(f"{rng} (baja de {_eur(floor)})")
        else:
            bonus += 3
            flags.append(rng)
    else:
        hit("salary_unknown", "salario no indicado", PENALTY["salary_unknown"])

    if location and not IN_SPAIN.search(location):
        hit("abroad", "fuera de España", PENALTY["abroad"])

    mode = facts.get("work_mode") or "presencial"
    local = matched_keyword(f"{location}\n{title}", cfg["locations"])
    if local:
        bonus += 10
        flags.append(f"en tu zona ({local})")
    if mode == "remoto":
        flags.append("remoto")
        if "remoto" in cfg["work_modes"]:
            bonus += 8
    elif mode == "hibrido":
        flags.append("híbrido")
    if mode not in cfg["work_modes"]:
        hit("mode", f"modalidad no deseada ({MODE_LABEL[mode]})", PENALTY["mode"])
    elif cfg["scope"] == "local" and mode != "remoto" and not local:
        hit("zone", "fuera de tu zona", PENALTY["zone"])

    if cfg["require_keywords"] and not matched_keyword(f"{title}\n{desc}", cfg["require_keywords"]):
        hit("require", f"no menciona {' / '.join(cfg['require_keywords'][:3])}", PENALTY["require"])
    bad = matched_keyword(title, cfg["exclude_keywords"])
    if bad:
        hit("exclude", f"excluida por «{bad}»", PENALTY["exclude"])

    # Portal choice is a plain switch, not a hardness rule: left out = discarded.
    portal = job.get("portal")
    if portal in PORTAL_LABEL and portal not in cfg["portals"]:
        label = f"portal no elegido ({PORTAL_LABEL[portal]})"
        excluded.append(label)
        flags.append(label)

    posted = job.get("posted_date")
    if cfg["max_age_days"] and posted:
        try:
            age = (today - date.fromisoformat(posted)).days
        except ValueError:
            age = 0
        if age > cfg["max_age_days"]:
            hit("age", f"publicada hace {age} días", PENALTY["age"])

    if job.get("rank_score") is not None:
        score, fit = job["rank_score"], job.get("fit") or "low"
    else:
        base = job.get("base_score")
        if base is None:
            base = base_score(title, desc)
        score = max(0, min(100, base + bonus - penalty))
        fit = "high" if score >= 70 else "medium" if score >= 45 else "low"
    if cfg["min_score"] and score < cfg["min_score"]:
        excluded.append(f"puntuación < {cfg['min_score']}")
    return {"score": score, "fit": fit, "flags": flags, "excluded": excluded, "soft": soft}
