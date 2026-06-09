# Industry Risk Radar — Risk Score Methodology (v2.0)

**Status: LOCKED.** Don't change weights, windows, the category set, or the theme→topic mapping
without bumping the version and recomputing history. Month-over-month deltas only mean something
if the formula stays constant.

This is the single source of truth for scoring. `build_data.py` implements exactly this. The page
only renders what it produces.

> **v2 change:** moved from raw Signal topics to **8 thematic risk categories** (for the radar) and
> the **10-sector** list, per the radar layout. Each theme aggregates several Signal topics.

---

## 1. Scope

- **Industries (10):** Automotive, Energy, Finance, FMCG, Healthcare, Media, Professional Services,
  Retail, Technology, Travel. Each bound to a Signal topic ID in `industries.json`.
- **Thematic categories (8):** Regulatory & legal, Financial & market, Operational & supply,
  Cyber & data, Environmental & climate, Governance & ethics, Product & safety, Labour & workforce.
  Each maps to 1–4 Signal topic IDs (see `industries.json → thematic_categories`).
- **Cadence:** monthly. **Primary window:** trailing 30 days. **Trend:** trailing 12 weeks.
- **Source:** Signal `explore` + `events`. Sentiment uses the platform default (`negative-bias`).

## 2. Inputs per (industry × theme)

A theme's series is the **sum of its member Signal topics**, filtered to the industry topic.

| Symbol | Meaning | Source |
|--------|---------|--------|
| `weekly` | 12-week article_count series for the theme | explore, `interval=week`, `include=[theme topic ids]` |
| `V` | trailing-30d volume (sum of last 5 weekly buckets) | derived from `weekly` |
| `Neg` | share of negative coverage (0–1) | explore, `sentiment` dimension |
| `Mag` | top event magnitude (`peak_mean_ratio`) tagged to the theme | events tool |

## 3. Component scores (each 0–100)

```
VolMomentum  = clamp(0,100, (mean(weekly[-5:]) / mean(weekly[all 12]) - 0.5) * 100)
Negativity   = Neg * 100
EventSeverity= clamp(0,100, 20 * log10(1 + Mag))
```
VolMomentum compares the last 5 weeks to the 12-week mean — at-norm = 50, double = 100, half = 0.

## 4. Theme score & industry roll-up

```
Theme score   = round( 0.40*VolMomentum + 0.35*Negativity + 0.25*EventSeverity ), clamped 3–99
Industry IRS  = round( Σ(theme_score · theme_volume) / Σ(theme_volume) )   # volume-weighted
sentiment_neg = Σ(Neg · theme_volume) / Σ(theme_volume)
volume_total  = Σ(theme_volume)
```
The radar plots the 8 theme scores. The headline number is IRS. **Weights fixed at 0.40/0.35/0.25.**

## 5. Bands & deltas

| IRS | Band | Colour |
|-----|------|--------|
| 0–39 | Low | Seafoam |
| 40–59 | Moderate | Sunshine |
| 60–79 | Elevated | Orange |
| 80–100 | High | Signal Red |

**Delta** = IRS this month − IRS last month, from the prior `/data/history/` snapshot. The page also
keeps 3 monthly snapshots in `months` so users can switch months; older months are archived
snapshots (no live pull).

## 6. Events ("what's driving it")

Top events from the `events` tool for the industry over 30 days, ranked by `peak_mean_ratio`. Each
stores title, date, magnitude, source/story counts, entities, matched themes, and a Signal article
link. The biggest event's magnitude feeds that theme's EventSeverity.

## 7. Theme → Signal topic mapping (locked)

| Theme | Signal topics |
|-------|---------------|
| Regulatory & legal | Regulation, Antitrust Laws |
| Financial & market | Profit Warnings, International Trade, Accounting Irregularities |
| Operational & supply | Supply Chain, Supply Chain Disruptions |
| Cyber & data | Cyber Attack, Cyber Security |
| Environmental & climate | Climate change, Carbon Emissions, Air Pollution |
| Governance & ethics | Corporate Controversy, Corporate Crisis, Corporate Litigation, Fraud |
| Product & safety | Product Recall, Reliability and Safety |
| Labour & workforce | Strikes, Corporate Downsizing |

IDs live in `industries.json`. Adjusting membership changes scores → bump the version.

## 8. Reproducibility rules

Same windows (30d / 12w), same 8 themes + mapping, same 10 sector bindings, same sentiment
aggregation (`negative-bias`), same weights (0.40/0.35/0.25). Archive every run to
`/data/history/YYYY-MM.json` before publishing.

## Changelog
- **v2.0** — thematic 8-category model (radar) + 10 sectors + theme→topic mapping; months archive.
- **v1.0** — raw Signal-topic categories, single-month bar layout.
