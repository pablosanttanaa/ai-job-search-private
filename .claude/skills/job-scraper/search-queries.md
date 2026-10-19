# Search Queries for Job Scraper

## Installed portal CLIs (primary for `/scrape`)

`/scrape` discovers every portal skill under `.agents/skills/*/SKILL.md` and runs its CLI first. Shipped country-agnostic CLIs include `linkedin-search` and `freehire-search`; Danish demos and any skill you add with `/add-portal` are included the same way. You do **not** need a matching `site:` line below for those CLIs to run.

The `site:` query templates in this file are the **WebSearch fallback** — for portals without a CLI, company career pages, or when a CLI fails.

**Language scope:** write every query category in every language listed in your CLAUDE.md Languages table (typically 1-2, sometimes more). A posting requiring a language you have *not* declared, as a job condition, is excluded before scoring; a posting requiring a *higher level* than you declared in a language you *do* work in is flagged for your own judgment, not excluded — see `04-job-evaluation.md`'s Language Gate, the single source of truth for this rule. Translate each category's keywords rather than machine-translating word-for-word (e.g. "Frontend Developer" -> "Desarrollador Frontend", not a literal word-for-word translation) if you work in more than one language.

## Search Sites

Primary (Spain job boards):
- **infojobs.net** - largest general job board in Spain
- **linkedin.com/jobs** - LinkedIn job listings (Spain); also covered by `linkedin-search` CLI
- **tecnoempleo.com** - IT-specific job board in Spain
- **es.indeed.com** - Indeed Spain

Secondary (company career pages via Google):
- Direct Google searches with `site:` filters for Odoo partners and consultancies

## Query Categories

Queries are written in Spanish (Pablo's declared working language), plus the English product/skill terms that Spanish postings use as-is (Odoo, Python). Combine each query with location terms where the site supports it; Pablo is open to all of Spain, on-site or remote.

### Priority 1: Odoo development

```
site:infojobs.net "desarrollador Odoo"
site:infojobs.net "programador Odoo"
site:tecnoempleo.com Odoo desarrollador
site:linkedin.com/jobs "desarrollador Odoo" España
site:linkedin.com/jobs "Odoo developer" España remoto
```

### Priority 2: ERP / IT consulting

```
site:infojobs.net "consultor ERP" Odoo
site:infojobs.net "consultor técnico" Odoo
site:tecnoempleo.com "consultor Odoo"
site:linkedin.com/jobs "consultor Odoo" España
site:linkedin.com/jobs "consultor IT" ERP España
```

### Priority 3: Python backend / integrations

```
site:infojobs.net "desarrollador Python" backend
site:tecnoempleo.com "desarrollador Python" remoto
site:linkedin.com/jobs "desarrollador Python" integraciones API España
```

### Priority 4: Broader technical

Wider net for related roles.

```
site:infojobs.net "analista programador" Python PostgreSQL
site:tecnoempleo.com "administrador de sistemas" AWS Linux junior
site:linkedin.com/jobs "consultor tecnológico" implantación software España
```

## Location Filter

Pablo is open to all of Spain, on-site or remote:
- Las Palmas de Gran Canaria / Canarias (ideal, home)
- Remote / telework anywhere in Spain (ideal)
- On-site anywhere in Spain (acceptable; relocation is fine)
- Outside Spain (flag, ask the user)

## Salary Filter

Hard floor: 26,000 EUR gross per year. When a posting states a salary below this, exclude it. When no salary is stated, include it and flag "salary not stated".

## Language Filter

Your working languages and levels are in CLAUDE.md's Languages table. When filtering scraped results, apply `04-job-evaluation.md`'s Language Gate: a posting requiring a language you haven't declared at all is excluded; a posting requiring a higher level than you declared in a language you do work in is not excluded, flag it clearly instead (see `job-scraper/SKILL.md`'s Step 3 "Quick Fit Assessment" for how the flag surfaces in `/scrape` output). Postings simply *written* in a language you don't work in, that don't require it on the job, are fine.

## Date Filter

Only include jobs posted within the last 14 days, or with an application deadline that has not yet passed. If a posting date cannot be determined, include it but flag as "date unknown".

## Adapting Queries

If the user specifies a focus area, select queries from the matching category and also generate 2-3 custom queries for that focus. For example:
- "/scrape [focus_area]" -> relevant category queries + custom focus-specific queries
