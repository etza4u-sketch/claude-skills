# AI Job Search — Bronze / Silver / Gold

Search for AI engineer jobs in Israel using the three-tier model:

| Tier | Description | Strategy |
|------|-------------|----------|
| 🥇 Gold | Hidden opportunities — funding rounds, new R&D centres, founding roles | Act early, reach out directly |
| 🥈 Silver | Semi-visible — fast-growing companies, senior roles at funded startups | Apply via recruiters or community |
| 🥉 Bronze | Public job board listings | Apply immediately, high competition |

## Installation

```bash
cd job-search-app
pip install -r requirements.txt
```

## Usage

```bash
# Full scan + report
python app.py scan

# Only Gold-tier jobs
python app.py scan --tier gold

# Only senior/unique positions with urgency ≥ 3.5
python app.py scan --senior --min-score 3.5

# Show funding signals → predicted future hiring
python app.py signals

# Explain the BSG model
python app.py explain

# Start daemon (hourly alerts + weekly report every Friday 09:00)
python app.py watch

# Export last scan to JSON
python app.py export --output my_jobs.json
```

## Architecture

```
app.py                  CLI entrypoint (Click + Rich)
config.py               Keywords, thresholds, feed URLs
searchers/
  base.py               Job dataclass + BaseSearcher
  drushim.py            drushim.co.il scraper
  indeed.py             il.indeed.com scraper
  rss.py                RSS/Atom feed reader
classifiers/
  seniority.py          Detects senior roles + urgency score
  bronze_silver_gold.py Assigns Bronze/Silver/Gold tier
signals/
  funding.py            Parses funding news → hiring predictions
  market.py             Aggregates trends + heat index
reports/
  generator.py          Rich tables, panels, alerts
scheduler/
  jobs.py               Schedule-based daemon
```

## Sources Scanned

- **drushim.co.il** — Israel's largest Hebrew job board
- **il.indeed.com** — Indeed Israel
- **RSS feeds** — Geektime, tech news, LinkedIn job feeds
- **Funding news** — TechCrunch Israel, Calcalist, Geektime

## Urgency Score (0–5)

- **+2.0** senior/lead/architect role
- **+0.3–0.5** per hot AI skill (LLM, RAG, GenAI, CV, MLOps…)
- **+0.5** recently published
- **+0.5** Gold tier bonus
- Immediate alert threshold: **≥ 3.5**
