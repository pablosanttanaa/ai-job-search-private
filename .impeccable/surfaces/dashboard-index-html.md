---
version: 1
slug: "dashboard-index-html"
primary_target: "dashboard/index.html"
related_targets: []
---

# Dashboard de ofertas

Scope: dashboard/index.html, the single daily screen. Mode: Operate.
Job: decide what to apply to today; open the best posting, download its ATS CV, apply. Used on desktop (daily review after the 13:00 search) and phone (quick checks).
Must not read as a generic SaaS dashboard (user's words).
Content: live-evaluated postings from /api/data (score, fit, alerts, excluded reasons, keywords), runs, requirements dialog, CV ATS links. All copy in Spanish.
Chosen composition: .impeccable/mocks/decision/assigned.html (code-led).

## Direction contract

THESIS: Every posting reads as a newspaper classified ad from the "Ofertas de empleo" section: job title as a bold condensed lead-in, the rest set run-in. Refuses the KPI-card + blue-chart SaaS arrangement; numbers and charts step behind the list.

OWN-WORLD: Process-yellow section band (#ffd200) with a 3px ink rule as the shell; cool off-white paper ground (#f4f3ef), dense ink (#16130f), one blue for links/actions (#1d4fd7), vermilion only for NUEVA and hard discards (#c8321e), amber for penalized. One family, Archivo, width axis doing the work: 62% width black for display and numerals, 75% for lead-ins, 100% for text. Square corners, rules instead of boxes; only the featured ad is framed (3px ink border). Dark theme = ink ground, yellow band kept.

STORY: He opens the page, sees today's best new posting framed at the top with its score, downloads its CV ATS in one click, then scans "Hoy" as a column of ads; anything older or filtered is one tab away, and why a posting is hidden is always stated.

FIRST VIEWPORT: Yellow band: title, tabs (Pendientes · Todas · Descartadas: the tabs switch posting status, and the first tab holds every pending posting, so it is named Pendientes; "Hoy" is the section heading for the latest search inside it, shown only when that search ran today in Madrid), folio date, last-search line, Requisitos, Buscar ahora. Left 1fr: framed featured ad (score at ~130px condensed black, title, company · place, short snippet, facts row, CV ATS primary + Abrir). Below, "Hoy" heading rule and classified rows (score numeral, bold lead-in + run-in text + alerts, mode · date, CV ATS · Abrir). Right 300px rail: "Tus requisitos" summary with count passing/hidden. Phone: band in two lines, filters in one scrolling row, featured actions side by side, rows set as a run-in column with mode · date and links on one line; rail moves below.

FORM: Anuncios por palabras (classifieds), candidate 5 of my ordered list; seed:647ddd10e7c787af. Signature move: the bold-caps classified lead-in on every row and the single framed "anuncio destacado". Raises: hierarchy by size contrast only (variable-font-specimen); list grouped by exact day with real age (labanotation); one score numeral at three fixed sizes (emigre-bitmap); opening a row expands in place and dims siblings (streaming wall); a defined mark for each state nueva/evaluada/penalizada/descartada/caducada (acetate manual). Motion: 180ms expand/dim only.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
