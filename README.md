# Signal AI — Industry Risk Radar

An interactive, embeddable landing page showing where reputational risk is concentrating across
10 industries each month, what's driving it, and the regulation to watch — powered by Signal AI
media data, with a web-sourced regulatory layer.

Hosted on GitHub → Vercel → embedded in Unbounce. Refreshes monthly via a reviewed pipeline.

## Architecture (the one rule)

The **page** (`public/`) only ever *reads* `data.json`. The **pipeline** (`pipeline/`) only ever
*writes* it. They never touch each other — so the data can refresh without touching the page, and
the page can't break on refresh.

```
monthly job → data.staging.json → human review → data.json → git push → Vercel deploy → Unbounce
```

## Structure

```
public/
  index.html        Interactive page: month picker, ranked industry rail, score + radar,
                    category bars, trend, events, regulatory toggle
  app.js            UI logic (reads window.__RISK_DATA__)
  data.js           The data, as window.__RISK_DATA__ — the app's integration point (auto-generated)
  data.json         Canonical copy of the same payload
  assets/           logo.png, tri.png
pipeline/
  methodology.md    LOCKED risk-score formula (v2.0) — source of truth for scoring
  industries.json   10 sectors + 8 thematic categories, each mapped to Signal topic IDs
  build_data.py     Reference implementation of methodology.md → emits data.js + data.json
  runbook.md        Monthly refresh steps + human-review gate + scheduled-task prompt
data/history/
  2026-06.json      Monthly score snapshots → powers month-over-month deltas
vercel.json
```

The monthly pipeline writes `public/data.js` (what the app loads) and `public/data.json` (canonical).
To refresh, the job regenerates these and commits — the page itself never changes.

## Local preview

Double-click `public/index.html` (it loads `data.js`, `app.js`, fonts + Chart.js from CDN — no
server needed), or serve it:
```
cd public && python3 -m http.server 8000   # → http://localhost:8000
```

## Deploy

1. Push this repo to GitHub.
2. Import into Vercel (Output Directory = `public`, or use the included `vercel.json`).
3. Embed the Vercel URL in Unbounce via an iframe.

## Monthly refresh

See `pipeline/runbook.md`. Driven by a Cowork scheduled task that pulls Signal data, drafts the
regulatory watchlist from the web, stages the result, and **waits for human approval** before
publishing.

## ⚠ Prototype data notice

This build ships with **real Signal data for Automotive** (pulled 2026-06-09) and **sample data for
the other 9 sectors** (flagged `seed:true`) plus **illustrative regulatory items**, so the layout is
fully demoable. The first live pipeline run replaces all of it. The on-page banner makes this
explicit per tab.

## Methodology (summary)

Industry Risk Score (0–100) = `0.40 × volume momentum + 0.35 × negativity + 0.25 × event severity`,
computed per **thematic category** (8 themes, each aggregating several Signal topics) and
volume-weighted into the industry score. The radar plots the 8 theme scores. Full detail, the locked
weights/windows, and the theme→topic mapping live in `pipeline/methodology.md` (v2.0). Regulatory
items are **not** from Signal — they are web-sourced and human-reviewed.
