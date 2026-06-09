# Monthly Refresh Runbook — Industry Risk Radar

This is the step-by-step the monthly job follows. It is designed to run as a **Cowork scheduled
task** (Claude has the Signal connector + web search) with a **human-in-the-loop review gate**
before anything goes live. Nothing publishes without sign-off.

**Cadence:** 1st working day of each month.
**Owner of the review gate:** Raquel (or delegate).

---

## Stage 1 — Pull Signal data (automated, no human)

For each of the 10 industries in `industries.json`, over the window ending on the run date. The 8
**thematic categories** each map to several Signal topics (`industries.json → thematic_categories`);
a theme's series is the sum of its member topics.

1. **Theme volumes + 12-week trend** — `explore`, filter `topics=[industry_topic]`,
   `dimension=topic` with `include=[ALL mapped theme topic IDs]`, `metric=article_count`,
   `interval=week`, window = trailing 12 weeks. One call per industry returns every topic's weekly
   series; sum into the 8 themes in code. Trailing-30d volume `V` = sum of the last 5 weekly buckets.
2. **Negativity** — `explore`, filter `topics=[industry_topic]` AND each theme's topics,
   `dimension=sentiment`. → negative share `Neg` per theme (default `negative-bias`).
3. **Events** — `events`, `topic_names=[industry]`, risk-term query, window = 30 days, `size=8`.
   → `Mag` (max `peak_mean_ratio`) per theme + the drill-down list.

Feed these into `build_data.py` (the locked implementation of `methodology.md` v2). It computes each
theme score, the volume-weighted Industry Risk Score, the radar, and the per-sector payload, then
writes `public/data.js` (the app's integration point) and `public/data.json` (canonical).

> The current `build_data.py` embeds Automotive's real numbers as a prototype seed (real
> volumes/trends; estimated per-theme negativity/event-severity). For production, replace the
> embedded blocks with freshly-pulled values for all 10 sectors (or have the task write an
> `inputs.json` the script reads). The scoring functions never change.

## Stage 2 — Regulatory web research (automated draft, human-reviewed)

Regulation does **not** come from Signal. For each industry:

1. Web-search authoritative sources only — the regulators themselves, government registers, and
   reputable law-firm regulatory trackers. Avoid blogs/secondary commentary.
2. Extract, per regulation: `name`, `jurisdiction`, `effective_date` (or deadline), one-line
   `summary`, and the `source` URL.
3. Bucket by date relative to run date: **3–6 months** → `window:"3-6m"`; **6–12 months** →
   `window:"6-12m"`. Drop anything outside 0–12 months or already in effect.
4. Mark every item `status:"draft"` until a human approves it.

## Stage 3 — Assemble & stage (automated)

1. Write the combined payload to `public/data.staging.json` (NOT `data.json`).
2. Archive the previous live file's scores to `data/history/<prev-month>.json` if not already
   archived. Deltas are computed against the most recent history snapshot.
3. Produce a short **review summary**: new/removed regulations, any IRS that moved > 10 points,
   any sector with a band change, and the top event per sector.

## Stage 4 — Human review gate 🔴 REQUIRED

Send the review summary to the chosen channel (email/Slack) with a link to the staged file.
Reviewer checks, at minimum:
- Every **regulatory** item: name, date, jurisdiction, and that the source URL is authoritative.
- Any **risk score** that moved hard or changed band — does the driving event justify it?
- Spelling of entity/company names on the prospect-facing drill-down.

**Review depth options** (pick one and set it in the task prompt):
- *Full* — read every regulatory item + every score.
- *Exception-only* — only items that are new, or scores that moved > X points; trust the rest.

On approval → continue. On changes → reviewer edits the staging file (or replies with fixes) and
the task re-stages.

## Stage 5 — Publish (after approval)

1. Promote `data.staging.json` → `public/data.json` (and regenerate `public/data.js`).
2. Commit + push to GitHub `main` (or open a PR the reviewer merges).
3. Vercel auto-deploys. The Unbounce embed now shows the new month. Done.

---

## Scheduled-task prompt (paste when wiring the task)

> Run the Industry Risk Radar monthly refresh per `pipeline/runbook.md`. Pull Signal data for all
> 10 industries (stage 1), draft the regulatory watchlist from authoritative web sources (stage 2),
> run `build_data.py`, archive history, and write `public/data.staging.json` (stage 3). Then send me
> a review summary at <channel> and STOP — do not publish. After I approve, promote staging to
> `data.json`, push to GitHub, and confirm the Vercel deploy.

Cron: `0 7 1 * *` (07:00 on the 1st of each month) — adjust to your timezone.

## What stays manual / one-time
- GitHub repo + Vercel project + Unbounce embed (accounts).
- Choosing notification channel and review depth.
- First-time replacement of the prototype's hard-coded Automotive block with live pulls for all 10.
