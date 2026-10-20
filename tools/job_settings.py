"""Search preferences edited from the dashboard (job_scraper/settings.json).

Shared by dashboard/server.py (GET/PUT /api/settings) and tools/daily_scrape.py
(scoring and queries), so both validate the file the same way. A missing or
invalid file falls back to DEFAULTS, which mirror the candidate profile.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETTINGS = ROOT / "job_scraper" / "settings.json"

MODES = ("presencial", "hibrido", "remoto")
MODE_LABEL = {"presencial": "presencial", "hibrido": "semipresencial", "remoto": "teletrabajo"}
SCOPES = ("spain", "local")

DEFAULTS = {
    "min_salary": 26000,
    # Keywords matched against the posting's location; the first one also
    # drives the local LinkedIn query.
    "locations": ["Canarias", "Las Palmas", "Gran Canaria", "Tenerife"],
    # Where on-site / hybrid roles are acceptable: anywhere in Spain, or only
    # in the locations above (remote roles are always location-free).
    "scope": "spain",
    "work_modes": list(MODES),
    "penalize_english": True,
    "exclude_keywords": [],
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


def validate(data) -> dict:
    """Return a clean settings dict or raise ValueError with a Spanish message."""
    if not isinstance(data, dict):
        raise ValueError("formato de ajustes no válido")
    merged = {**DEFAULTS, **{k: v for k, v in data.items() if k in DEFAULTS}}

    sal = merged["min_salary"]
    if isinstance(sal, str) and sal.strip().isdigit():
        sal = int(sal)
    if isinstance(sal, bool) or not isinstance(sal, int) or not 0 <= sal <= 300000:
        raise ValueError("el salario mínimo debe ser un número entre 0 y 300.000")

    locations = _str_list(merged["locations"], "ubicación", 15, 60)
    scope = merged["scope"]
    if scope not in SCOPES:
        raise ValueError("alcance no válido")
    if scope == "local" and not locations:
        raise ValueError("indica al menos una ubicación para buscar solo en tu zona")

    modes = merged["work_modes"]
    if not isinstance(modes, list) or not modes or any(m not in MODES for m in modes):
        raise ValueError("elige al menos un tipo de trabajo")

    if not isinstance(merged["penalize_english"], bool):
        raise ValueError("«penalizar inglés» debe ser sí o no")

    return {
        "min_salary": sal,
        "locations": locations,
        "scope": scope,
        "work_modes": [m for m in MODES if m in modes],
        "penalize_english": merged["penalize_english"],
        "exclude_keywords": _str_list(merged["exclude_keywords"], "palabras excluidas", 30, 40),
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
