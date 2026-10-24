"""Search preferences edited from the dashboard (job_scraper/settings.json).

Shared by dashboard/server.py (GET/PUT /api/settings), tools/daily_scrape.py
(queries) and tools/job_rules.py (filtering and scoring), so all of them
validate the file the same way. A missing or invalid file falls back to
DEFAULTS, which mirror the candidate profile.

Every requirement has a hardness level in `rules` (off / soft / hard, see
tools/job_rules.py). Files saved before rules existed are upgraded on load:
`penalize_english` becomes the English rule and the rest take the defaults.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "job_scraper" / "settings.json"

MODES = ("presencial", "hibrido", "remoto")
# Portals the unattended scrape (tools/daily_scrape.py) can query.
PORTALS = ("linkedin-search", "freehire-search")
SCOPES = ("spain", "local")
LEVELS = ("off", "soft", "hard")
RULES = ("years", "senior", "english", "other_lang", "salary", "salary_unknown",
         "mode", "zone", "abroad", "require", "exclude", "age")

DEFAULT_RULES = {
    "years": "hard",
    "senior": "hard",
    "english": "soft",
    "other_lang": "hard",
    "salary": "hard",
    "salary_unknown": "off",
    "mode": "hard",
    "zone": "hard",
    "abroad": "hard",
    "require": "off",
    "exclude": "hard",
    "age": "soft",           # no effect while max_age_days is 0
}

DEFAULTS = {
    "min_salary": 26000,
    # Keywords matched against the posting's location; the first one also
    # drives the local LinkedIn query.
    "locations": ["Canarias", "Las Palmas", "Gran Canaria", "Tenerife"],
    # Where on-site / hybrid roles are acceptable: anywhere in Spain, or only
    # in the locations above (remote roles are always location-free).
    "scope": "spain",
    "work_modes": list(MODES),
    # Postings from a portal left out are neither searched nor shown.
    "portals": list(PORTALS),
    "max_years": 2,
    "require_keywords": [],
    "exclude_keywords": [],
    "max_age_days": 0,       # 0 = no limit
    "min_score": 0,          # 0 = show every score
    "rules": DEFAULT_RULES,
}


def _str_list(value, field: str, max_items: int, max_len: int) -> list[str]:
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, list):
        raise ValueError(f"«{field}» debe ser una lista")
    items = []
    for v in value:
        if not isinstance(v, str):
            raise ValueError(f"«{field}» solo admite texto")
        v = " ".join(v.split())
        if not v:
            continue
        if len(v) > max_len:
            raise ValueError(f"«{v[:20]}…» es demasiado largo (máx. {max_len} caracteres)")
        if v.lower() not in (i.lower() for i in items):
            items.append(v)
    if len(items) > max_items:
        raise ValueError(f"«{field}» admite como mucho {max_items} elementos")
    return items


def _int(value, field: str, lo: int, hi: int) -> int:
    if isinstance(value, str) and value.strip().isdigit():
        value = int(value)
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
        raise ValueError(f"{field} debe ser un número entre {lo:,} y {hi:,}".replace(",", "."))
    return value


def validate(data) -> dict:
    """Return a clean settings dict or raise ValueError with a Spanish message."""
    if not isinstance(data, dict):
        raise ValueError("formato de ajustes no válido")
    merged = {**DEFAULTS, **{k: v for k, v in data.items() if k in DEFAULTS}}

    rules_in = merged["rules"]
    if not isinstance(rules_in, dict):
        raise ValueError("«niveles de dureza» no válidos")
    rules = dict(DEFAULT_RULES)
    if "rules" not in data and data.get("penalize_english") is False:
        rules["english"] = "off"
    for name, level in rules_in.items():
        if name not in RULES:
            continue
        if level not in LEVELS:
            raise ValueError(f"nivel de dureza no válido para «{name}»")
        rules[name] = level

    sal = _int(merged["min_salary"], "el salario mínimo", 0, 300000)
    locations = _str_list(merged["locations"], "ubicación", 15, 60)
    scope = merged["scope"]
    if scope not in SCOPES:
        raise ValueError("alcance no válido")
    if scope == "local" and not locations:
        raise ValueError("indica al menos una ubicación para buscar solo en tu zona")

    portals = merged["portals"]
    if not isinstance(portals, list) or not portals or any(p not in PORTALS for p in portals):
        raise ValueError("elige al menos un portal")

    modes = merged["work_modes"]
    if not isinstance(modes, list) or not modes or any(m not in MODES for m in modes):
        raise ValueError("elige al menos un tipo de trabajo")

    require = _str_list(merged["require_keywords"], "palabras obligatorias", 20, 40)
    if rules["require"] != "off" and not require:
        raise ValueError("indica al menos una palabra obligatoria o pon esa regla en «No filtrar»")

    return {
        "min_salary": sal,
        "locations": locations,
        "scope": scope,
        "work_modes": [m for m in MODES if m in modes],
        "portals": [p for p in PORTALS if p in portals],
        "max_years": _int(merged["max_years"], "los años máximos", 0, 20),
        "require_keywords": require,
        "exclude_keywords": _str_list(merged["exclude_keywords"], "palabras excluidas", 30, 40),
        "max_age_days": _int(merged["max_age_days"], "la antigüedad máxima", 0, 365),
        "min_score": _int(merged["min_score"], "la puntuación mínima", 0, 100),
        "rules": rules,
    }


def load(path: Path = SETTINGS) -> dict:
    try:
        return validate(json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError:
        return validate({})
    except (json.JSONDecodeError, ValueError) as exc:
        print(f"settings.json no válido ({exc}); uso los valores por defecto")
        return validate({})


def save(cfg: dict, path: Path = SETTINGS) -> dict:
    clean = validate(cfg)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)
    return clean
