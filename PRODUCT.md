# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
One user: Pablo Santana Susilla, a junior Odoo developer (Python, PostgreSQL) in Las Palmas de Gran Canaria, employed and quietly looking for his next role in Spain. He uses the dashboard on desktop for a calm daily review after the automatic 13:00 search, and on his phone for quick checks of whether anything new arrived.

## Product Purpose
A private job-search dashboard that turns daily portal scrapes (LinkedIn, freehire) into a short, honest list of postings worth applying to. Success: each day he can see in seconds which new postings meet his requirements, open the best one, download a tailored ATS CV and apply.

## Positioning
Not a job board: a personal filter. Every posting is scored against his own CV and judged by requirements he sets himself, each with a hardness level (ignore / penalize / discard), re-applied live to every posting already found. The CV button produces an ATS-friendly CV tailored to that posting from his real profile only.

## Operating Context
- Served by `dashboard/server.py` (Python stdlib) behind Caddy basic auth on an Oracle VPS; single static page `dashboard/index.html` with inline CSS/JS and a small JSON API.
- A systemd timer runs the scrape daily at 13:00 Madrid time; a button launches one manually (2-4 minutes).
- Postings may also be evaluated in depth by the `/rank` Claude skill (rank_score, verdict, strengths, gaps), which the dashboard shows.
- Downstream workflow in this repo: `/apply` for full CV + cover letter, `/interview` for prep.

## Capabilities and Constraints
- Live evaluation per posting: score, fit band (alto / medio / bajo), alerts, and which requirements it breaks.
- Requirements dialog with presets (Flexible / Equilibrado / Estricto) and per-rule hardness.
- "Nueva" marking for postings found in the latest successful run.
- ATS CV PDF per posting (`/api/cv/<key>.pdf`), with matched and missing keywords.
- Statuses: sin evaluar, evaluada, descartada, caducada, no disponible.
- No build step, no external runtime dependencies on the server; the page must work served as a single file.
- All copy in Spanish (es-ES dates and euro amounts).

## Evidence on Hand
Real data only: `job_scraper/seen_jobs.json` (on the VPS ~170 postings), `job_scraper/runs.json`. No testimonials or claims; nothing to fabricate.

## Product Principles
1. The daily decision comes first: what is new, what fits, what to do next. Everything else is secondary.
2. Honest filtering: show why a posting is hidden or penalized; never silently drop data.
3. Works equally for a quick phone glance and a focused desktop review.
4. The CV and the scoring never invent experience the profile does not have.
