#!/usr/bin/env python3
"""ATS-friendly CV, tailored to one posting in job_scraper/seen_jobs.json.

The content comes only from cv/ats_base.json (facts from the candidate
profile). Tailoring is deterministic and never invents anything:
  - the posting's title goes in as the target role,
  - the skills the posting asks for and the CV has are listed first, with a
    line naming them in the summary,
  - inside each job, the bullets that cover those skills move up,
  - skills the posting asks for and the CV lacks are reported as gaps, never
    added.

The PDF is written with the standard library only (so it also runs on the VPS,
which has no LaTeX): one column, standard Spanish section headings, Helvetica
with WinAnsi encoding, contact details as literal text, no icons, tables or
images - every word sits in the text layer in reading order.

Usage:
    python tools/ats_cv.py <job-key> [-o cv/ats/<key>.pdf] [--text] [--state PATH]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / "cv" / "ats_base.json"
STATE = ROOT / "job_scraper" / "seen_jobs.json"

# tag -> (label shown to the candidate, pattern searched in the posting).
# Tags used in cv/ats_base.json are skills the CV covers; the others exist so a
# posting asking for them shows up as a gap.
KEYWORDS = {
    "odoo": ("Odoo", r"odoo"),
    "orm": ("ORM de Odoo", r"\borm\b"),
    "python": ("Python", r"python"),
    "postgresql": ("PostgreSQL", r"postgre"),
    "sql": ("SQL", r"\bsql\b"),
    "xml": ("XML", r"\bxml\b(?!-rpc)"),
    "qweb": ("QWeb", r"qweb"),
    "security": ("Seguridad y permisos", r"reglas de (?:acceso|seguridad)|permisos|access rights|record rules"),
    "rest": ("API REST", r"\brest(?:ful)?\b"),
    "xmlrpc": ("XML-RPC / JSON-RPC", r"xml-?rpc|json-?rpc"),
    "api": ("APIs", r"\bapis?\b"),
    "integration": ("Integraciones", r"integraci|integrat"),
    "migration": ("Migración de datos", r"migraci|migrat"),
    "erp": ("ERP", r"\berp\b"),
    "implementation": ("Implantación", r"implanta|implementa|implementation"),
    "requirements": ("Análisis de requisitos", r"requisitos|requirements|an[aá]lisis funcional"),
    "functional": ("Perfil funcional", r"funcional|functional"),
    "consulting": ("Consultoría", r"consultor|consulting|consultant"),
    "accounting": ("Contabilidad", r"contab|accounting|financ"),
    "compliance": ("Cumplimiento normativo", r"normativ|compliance|regulator"),
    "modules": ("Módulos a medida", r"m[oó]dulos?|modules?|desarrollos? a medida|custom"),
    "data_model": ("Modelado de datos", r"modelo de datos|modelado|data model"),
    "aws": ("AWS", r"\baws\b|amazon web"),
    "cloud": ("Cloud", r"\bcloud\b|nube"),
    "linux": ("Linux", r"linux|ubuntu|debian"),
    "deploy": ("Despliegues", r"despliegue|deploy"),
    "git": ("Git", r"\bgit\b|github|gitlab"),
    "javascript": ("JavaScript", r"javascript|\bjs\b"),
    "frontend": ("Frontend", r"front-?end"),
    "laravel": ("Laravel", r"laravel"),
    "php": ("PHP", r"\bphp\b"),
    "support": ("Soporte e incidencias", r"soporte|incidencias|support"),
    "networking": ("Redes", r"\bredes\b|networking|cisco"),
    # gaps only
    "docker": ("Docker", r"docker|contenedores|container"),
    "kubernetes": ("Kubernetes", r"kubernetes|\bk8s\b"),
    "owl": ("OWL (Odoo Web Library)", r"\bowl\b"),
    "odoo_sh": ("Odoo.sh", r"odoo\.sh"),
    "ci": ("CI/CD", r"ci/cd|\bci\b|jenkins|github actions|gitlab ci"),
    "testing": ("Tests automatizados", r"\btests?\b|testing|unittest|pytest"),
    "django": ("Django", r"django"),
    "flask": ("Flask / FastAPI", r"flask|fastapi"),
    "react": ("React / Vue", r"react|vue|angular"),
    "java": ("Java", r"\bjava\b"),
    "dotnet": (".NET / C#", r"\.net\b|c#"),
    "scrum": ("Scrum / Agile", r"scrum|agile|[aá]gil"),
    "english": ("Inglés", r"ingl[eé]s|english"),
}
_PATTERNS = {tag: re.compile(rx, re.I) for tag, (_, rx) in KEYWORDS.items()}


# --- tailoring ------------------------------------------------------------

def load_base(path: Path = BASE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def posting_tags(job: dict) -> list[str]:
    text = "\n".join(filter(None, [job.get("title"), job.get("description") or job.get("snippet")]))
    return [tag for tag, rx in _PATTERNS.items() if rx.search(text)]


def cv_tags(base: dict) -> set[str]:
    tags = {t for s in base["skills"] for t in s["tags"]}
    tags |= {t for e in base["experience"] for b in e["bullets"] for t in b["tags"]}
    return tags


def analyze(job: dict, base: dict | None = None) -> dict:
    """Posting keywords the CV covers and the ones it does not (labels)."""
    base = base or load_base()
    have = cv_tags(base)
    wanted = posting_tags(job)
    # "Inglés" is a language gap, handled by the settings rules, not a skill.
    return {
        "matched": [KEYWORDS[t][0] for t in wanted if t in have],
        "missing": [KEYWORDS[t][0] for t in wanted if t not in have and t != "english"],
        "tags": [t for t in wanted if t in have],
    }


def _span(start: str, today: date) -> str:
    y, m, _ = map(int, start.split("-"))
    months = (today.year - y) * 12 + today.month - m
    years, months = divmod(max(months, 0), 12)
    parts = []
    if years:
        parts.append(f"{years} año{'s' if years > 1 else ''}")
    if months:
        parts.append(f"{months} mes{'es' if months > 1 else ''}")
    return " y ".join(parts) or "menos de un mes"


def target_role(title: str) -> str:
    """The posting title without portal noise ("… | Hybrid", "(Remoto)", "- Madrid")."""
    title = re.split(r"\s+[|]\s+", title)[0]
    title = re.sub(r"\s*[(\[][^)\]]*(?:remot|h[ií]brid|hybrid|presencial|m/f|h/m|f/m)[^)\]]*[)\]]", "", title, flags=re.I)
    return " ".join(title.split())


def build(job: dict, base: dict, today: date) -> dict:
    """The tailored CV as plain data (rendered by to_pdf / to_text)."""
    info = analyze(job, base)
    wanted = info["tags"]
    rank = {t: i for i, t in enumerate(wanted)}

    def relevance(tags: list[str]) -> tuple[int, int]:
        hits = [rank[t] for t in tags if t in rank]
        return (-len(hits), min(hits) if hits else 99)

    skills = [s["label"] for s in sorted(base["skills"], key=lambda s: relevance(s["tags"]))]
    summary = [s.format(dev_years=_span(base["dev_start"], today), total_years=_span(base["experience_start"], today))
               for s in base["summary"]]
    if info["matched"]:
        summary.insert(-1, "Experiencia directa en lo que pide esta oferta: " + ", ".join(info["matched"][:8]) + ".")
    experience = []
    for e in base["experience"]:
        bullets = sorted(e["bullets"], key=lambda b: relevance(b["tags"]))
        experience.append({**e, "bullets": [b["text"] for b in bullets]})
    return {
        "name": base["name"],
        "headline": base["headline"],
        "target": target_role(job.get("title") or ""),
        "contact": base["contact"],
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "education": base["education"],
        "certifications": base["certifications"],
        "languages": base["languages"],
        "analysis": {k: info[k] for k in ("matched", "missing")},
    }


def to_text(cv: dict) -> str:
    c = cv["contact"]
    out = [cv["name"], cv["headline"], f"{c['location']} | {c['email']}", c["linkedin"], c["availability"], ""]
    out += ["PERFIL PROFESIONAL", f"Objetivo: {cv['target']}", *cv["summary"], ""]
    out += ["COMPETENCIAS TÉCNICAS", ", ".join(cv["skills"]), ""]
    out.append("EXPERIENCIA PROFESIONAL")
    for e in cv["experience"]:
        out += [e["title"], f"{e['company']} | {e['location']} | {e['start']} – {e['end']}", *[f"• {b}" for b in e["bullets"]], ""]
    out.append("FORMACIÓN")
    for ed in cv["education"]:
        out += [ed["title"], f"{ed['school']} | {ed['dates']}"]
    out += ["", "CERTIFICACIONES", " · ".join(cv["certifications"]), "", "IDIOMAS", " · ".join(cv["languages"])]
    return "\n".join(out) + "\n"


# --- PDF ------------------------------------------------------------------

# Standard Helvetica / Helvetica-Bold advance widths for ASCII 32..126 (AFM).
_HELV = [278, 278, 355, 556, 556, 889, 667, 191, 333, 333, 389, 584, 278, 333, 278, 278,
         556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 278, 278, 584, 584, 584, 556,
         1015, 667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833, 722, 778,
         667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 278, 278, 278, 469, 556,
         333, 556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833, 556, 556,
         556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500, 334, 260, 334, 584]
_BOLD = [278, 333, 474, 556, 556, 889, 722, 238, 333, 333, 389, 584, 278, 333, 278, 278,
         556, 556, 556, 556, 556, 556, 556, 556, 556, 556, 333, 333, 584, 584, 584, 611,
         975, 722, 722, 722, 722, 667, 611, 778, 722, 278, 556, 722, 611, 833, 722, 778,
         667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611, 333, 278, 333, 584, 556,
         333, 556, 611, 556, 611, 556, 333, 611, 611, 278, 278, 556, 278, 889, 611, 611,
         611, 611, 389, 556, 333, 611, 556, 778, 556, 556, 500, 389, 280, 389, 584]
_SPECIAL = {"–": 556, "—": 1000, "•": 350, "·": 278, "€": 556, "«": 556, "»": 556, "¿": 611,
            "¡": 333, "“": 333, "”": 333, "‘": 222, "’": 222, "…": 1000, "º": 365, "ª": 370}

A4_W, A4_H = 595.28, 841.89
MARGIN_X, MARGIN_TOP, MARGIN_BOTTOM = 48, 44, 44
TEXT_W = A4_W - 2 * MARGIN_X


def _width(text: str, size: float, bold: bool) -> float:
    table = _BOLD if bold else _HELV
    total = 0
    for ch in text:
        if ch in _SPECIAL:
            total += _SPECIAL[ch]
            continue
        base = unicodedata.normalize("NFD", ch)[0]
        o = ord(base)
        total += table[o - 32] if 32 <= o <= 126 else 556
    return total * size / 1000


def _wrap(text: str, size: float, bold: bool, width: float) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}" if cur else word
        if cur and _width(trial, size, bold) > width:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines or [""]


def _pdf_str(text: str) -> bytes:
    raw = text.encode("cp1252", errors="replace")
    return b"(" + raw.replace(b"\\", b"\\\\").replace(b"(", b"\\(").replace(b")", b"\\)") + b")"


def _info_str(text: str) -> bytes:
    return b"<FEFF" + text.encode("utf-16-be").hex().upper().encode() + b">"


class _Layout:
    def __init__(self, squeeze: float = 1.0) -> None:
        self.squeeze = squeeze               # < 1 tightens line and section spacing
        self.pages: list[list[bytes]] = []
        self._new_page()

    def _new_page(self) -> None:
        self.ops: list[bytes] = []
        self.pages.append(self.ops)
        self.y = A4_H - MARGIN_TOP

    def ensure(self, height: float) -> None:
        if self.y - height < MARGIN_BOTTOM:
            self._new_page()

    def text(self, x: float, s: str, size: float, bold: bool = False, gray: float = 0, tw: float = 0) -> None:
        # tw = extra word spacing (Tw); the spaces stay real characters, so the
        # text layer ATS parsers read is the same as for ragged text.
        font = b"/F2" if bold else b"/F1"
        self.ops.append(b"BT %s %.1f Tf %.3f Tw %.3f g %.2f %.2f Td %s Tj ET" % (font, size, tw, gray, x, self.y, _pdf_str(s)))

    def para(self, s: str, size: float = 10, bold: bool = False, indent: float = 0, lead: float = 1.38,
             bullet: str | None = None, gray: float = 0, after: float = 0, justify: bool = False) -> None:
        width = TEXT_W - indent
        lines = _wrap(s, size, bold, width)
        step = size * lead * self.squeeze
        for i, line in enumerate(lines):
            self.ensure(step)
            self.y -= step
            if bullet and i == 0:
                self.text(MARGIN_X + indent - 10, bullet, size, bold, gray)
            tw = 0.0
            if justify and i < len(lines) - 1 and line.count(" "):   # last line stays ragged
                tw = (width - _width(line, size, bold)) / line.count(" ")
            self.text(MARGIN_X + indent, line, size, bold, gray, tw)
        self.y -= after * self.squeeze

    def heading(self, s: str) -> None:
        self.ensure(50)                      # heading + rule + two lines of body
        self.y -= 19 * self.squeeze
        self.text(MARGIN_X, s.upper(), 10.5, True)
        self.y -= 4
        self.ops.append(b"0.6 G 0.6 w %.2f %.2f m %.2f %.2f l S" % (MARGIN_X, self.y, A4_W - MARGIN_X, self.y))
        self.y -= 2

    def streams(self) -> list[bytes]:
        return [b"\n".join(ops) for ops in self.pages]


def to_pdf(cv: dict) -> bytes:
    """One page when a slightly tighter type fits it, else the regular two."""
    for body, squeeze in ((9.5, 1.0), (9.25, 0.94), (9.0, 0.9)):
        streams = _render(cv, body, squeeze)
        if len(streams) == 1:
            break
    else:
        streams = _render(cv, 9.5, 1.0)
    return _write_pdf(streams, title=f"CV {cv['name']} – {cv['target']}", author=cv["name"])


def _render(cv: dict, BODY: float, squeeze: float) -> list[bytes]:
    SMALL = BODY - 0.5
    lay = _Layout(squeeze)
    c = cv["contact"]
    lay.y -= 4
    lay.para(cv["name"], 20, True, lead=1.0, after=6)
    lay.para(cv["headline"], 11.5, gray=0.25, after=2)
    lay.para(f"{c['location']} | {c['email']} | {c['linkedin']}", SMALL, gray=0.2, lead=1.3)
    lay.para(c["availability"], SMALL, gray=0.2, lead=1.3)

    lay.heading("Perfil profesional")
    lay.para(f"Objetivo: {cv['target']}", BODY, True, after=2)
    lay.para(" ".join(cv["summary"]), BODY, lead=1.32, justify=True)

    lay.heading("Competencias técnicas")
    lay.para(", ".join(cv["skills"]) + ".", BODY, lead=1.32, justify=True)

    lay.heading("Experiencia profesional")
    for i, e in enumerate(cv["experience"]):
        lay.ensure(60)                       # role + company line + first bullet stay together
        if i:
            lay.y -= 4
        lay.para(e["title"], BODY + 0.5, True)
        lay.para(f"{e['company']} | {e['location']} | {e['start']} – {e['end']}", SMALL, gray=0.3, after=1)
        for b in e["bullets"]:
            lay.para(b, BODY, indent=12, bullet="•", lead=1.28, justify=True)

    lay.heading("Formación")
    for ed in cv["education"]:
        lay.ensure(30)
        lay.para(ed["title"], BODY, True)
        lay.para(f"{ed['school']} | {ed['dates']}", SMALL, gray=0.3, after=3)

    lay.heading("Certificaciones")
    lay.para(" · ".join(cv["certifications"]), BODY, lead=1.32, justify=True)

    lay.heading("Idiomas")
    lay.para(" · ".join(cv["languages"]), BODY, lead=1.32)

    return lay.streams()


def _write_pdf(streams: list[bytes], title: str, author: str) -> bytes:
    objs: list[bytes] = []                    # objs[i] is object number i + 1
    font = b"<< /Type /Font /Subtype /Type1 /BaseFont /%s /Encoding /WinAnsiEncoding >>"
    objs.append(b"<< /Type /Catalog /Pages 2 0 R /Lang (es-ES) >>")
    objs.append(b"")                          # pages, filled below
    objs.append(font % b"Helvetica")
    objs.append(font % b"Helvetica-Bold")
    page_ids = []
    for s in streams:
        objs.append(b"<< /Length %d >>\nstream\n%s\nendstream" % (len(s) + 1, s))
        content_id = len(objs)
        objs.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] /Contents %d 0 R "
                    b"/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> >>" % (A4_W, A4_H, content_id))
        page_ids.append(len(objs))
    objs[1] = b"<< /Type /Pages /Kids [%s] /Count %d >>" % (b" ".join(b"%d 0 R" % p for p in page_ids), len(page_ids))
    objs.append(b"<< /Title %s /Author %s /Producer (tools/ats_cv.py) >>" % (_info_str(title), _info_str(author)))
    info_id = len(objs)

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (i, body)
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    out += b"".join(b"%010d 00000 n \n" % o for o in offsets)
    out += b"trailer\n<< /Size %d /Root 1 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, info_id, xref)
    return bytes(out)


def filename(job: dict, base: dict) -> str:
    slug = lambda s: re.sub(r"[^A-Za-z0-9]+", "_", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()).strip("_")
    return f"CV_{slug(base['name'])}_{slug(job.get('company') or 'oferta')[:40]}.pdf"


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("key", help="clave de la oferta en seen_jobs.json")
    ap.add_argument("-o", "--out", type=Path, help="ruta del PDF (por defecto cv/ats/<clave>.pdf)")
    ap.add_argument("--text", action="store_true", help="imprimir el texto del CV en vez de escribir el PDF")
    ap.add_argument("--state", type=Path, default=STATE)
    args = ap.parse_args()

    seen = json.loads(args.state.read_text(encoding="utf-8")).get("seen", {})
    job = seen.get(args.key)
    if job is None:
        print(f"No existe la oferta «{args.key}» en {args.state}", file=sys.stderr)
        return 1
    base = load_base()
    cv = build(job, base, date.today())
    if args.text:
        print(to_text(cv), end="")
    else:
        out = args.out or ROOT / "cv" / "ats" / f"{args.key}.pdf"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(to_pdf(cv))
        print(f"CV escrito en {out}")
    a = cv["analysis"]
    print(f"Cubre: {', '.join(a['matched']) or '—'}")
    print(f"No tienes (no se añade): {', '.join(a['missing']) or '—'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
