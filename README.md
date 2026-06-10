# Morocco World Cup 2026 AI Squad Analyzer

Real Football Data Pipeline + AI Squad Analyzer for evaluating Morocco's 2026 World Cup squad pool.

This project is designed to be credible, source-aware and honest about missing data. It does not invent football statistics. If a source is unavailable, not configured or not legally collectable, the value stays `N/A`.

## What The App Does

- Maintains an initial Moroccan player seed list in `data/players_seed.csv`.
- Enriches players through a real-data collector pipeline.
- Stores collected data in a local SQLite cache.
- Tracks `data_source`, `source_url`, `last_updated`, `reliability` and collection logs.
- Scores players only when enough real fields are available.
- Generates tactical lineups for:
  - 4-2-3-1
  - 4-3-3
  - 3-4-3
  - 4-4-2
  - 3-5-2
- Exports an AI-assisted PDF report.
- Shows a `Data Sources & Reliability` page with missing-data, stale-data and incoherence checks.

## Real Data Policy

The project follows these rules:

- No invented stats.
- Missing data is displayed as `N/A`.
- Every collected value must carry a source and update date.
- Scraping is disabled unless the source URL/access is explicitly configured and allowed.
- API sources are preferred over scraping.
- AI analysis must say when data is insufficient.

## Current Source Strategy

| Source | Status | Notes |
| --- | --- | --- |
| TheSportsDB | Implemented | Uses the free V1 `searchplayers.php` endpoint by player name. Collects profile, club/team when available, nationality, status, position and player image. |
| API-Football via RapidAPI | Implemented | Requires `API_FOOTBALL_KEY`. Collects player profile/stat fields returned by the provider. |
| FBref | Implemented | `collectors/fbref_player_stats_scraper.py` scrapes Standard, Shooting, Passing, Pass Types, GCA, Defense, Possession, Playing Time and Misc tables using the widget/page pattern from the notebook. Some environments receive FBref anti-bot pages; failures are logged and fallbacks continue. |
| SofaScore | Implemented | Uses the public HTTP API pattern from `tunjayoff/sofascore_scraper`: browser-like headers, per-player JSON cache, endpoint retries, 429 backoff and normalized CSV export. Some environments receive `403`; failures are logged and fallbacks continue. |
| FotMob | Scaffolded | Disabled by default. Enable only with permitted API/access. |
| Transfermarkt | Implemented | Uses `requests` + `BeautifulSoup` with player slugs. Extracts bio, club, contract, market value and profile metadata when Transfermarkt serves the page. |
| WhoScored | Scaffolded | Disabled by default due dynamic/session-heavy pages. |
| Understat | Scaffolded | Disabled until permitted IDs/endpoints are configured. |
| StatsBomb Open Data | Scaffolded | Open match-event data, not universal season player data. Needs competition/match config. |
| Football-Data.co.uk | Scaffolded | Mostly team/match CSVs, not player-level stats. Logged as unavailable for player enrichment. |

## Data Fields

The pipeline targets:

- club
- age
- position
- league
- matches played
- minutes played
- goals
- assists
- clean sheets
- xG / xA
- average rating
- injury status
- market value
- transfer history
- recent form
- offensive and defensive actions

Availability depends entirely on configured sources.

## Project Structure

```text
.
├── app.py
├── data/
│   ├── players_seed.csv
│   └── seed_players.csv              # legacy demo seed kept for reference
│   ├── fbref_raw/                    # raw FBref CSV cache
│   ├── processed/                    # cleaned merged CSV exports
│   └── cache/squad_data.sqlite       # local SQLite cache, ignored by Git
├── morocco_ai_squad/
│   ├── collectors/
│   │   ├── fbref_player_stats_scraper.py
│   │   ├── api_football_collector.py
│   │   ├── fbref_collector.py
│   │   ├── football_data_collector.py
│   │   ├── fotmob_collector.py
│   │   ├── sofascore_collector.py
│   │   ├── statsbomb_open_data_collector.py
│   │   ├── transfermarkt_collector.py
│   │   ├── understat_collector.py
│   │   └── whoscored_collector.py
│   ├── database/
│   │   ├── db.py
│   │   └── models.py
│   ├── services/
│   │   ├── data_merger.py
│   │   ├── data_quality.py
│   │   ├── player_scoring.py
│   │   └── tactical_ai.py
│   ├── ai_analysis.py
│   ├── charts.py
│   ├── config.py
│   ├── data_loader.py
│   ├── report.py
│   ├── scoring.py
│   ├── tactics.py
│   └── ui.py
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

## Standalone Scraping Pipeline

The repository includes an Edd Webster-style notebook/script pipeline:

```bash
python moroccan_players_scraper.py
```

Main outputs:

- `data/raw/fbref_moroccan_wc26.csv`
- `data/raw/transfermarkt_moroccan_wc26.csv`
- `data/raw/capology_moroccan_wc26.csv`
- `data/raw/whoscored_moroccan_wc26.csv`
- `data/processed/moroccan_players_wc26_master.csv`
- `data/cache/squad_data.sqlite`

Notebook:

- `Moroccan_Players_WC26_Scraping.ipynb`

The script follows the reference notebook style: `requests`, `BeautifulSoup`, `pandas.read_html()`, `tqdm` progress bars, cache checks, source-specific rate limits, exponential backoff for HTTP 429, raw CSV exports and a processed master table. Missing source IDs or blocked pages are logged and kept as `N/A`; no statistics are invented.

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## API-Football Configuration

Create `.env` from `.env.example` and add:

```env
API_FOOTBALL_KEY=your_rapidapi_key
RAPIDAPI_HOST=api-football-v1.p.rapidapi.com
```

Then open the app and click `Refresh Real Data`.

## FBref Configuration

Add a public player page URL in `data/players_seed.csv`:

```csv
player_id,player_name,...,fbref_url,...
df_hakimi,Achraf Hakimi,...,https://fbref.com/en/players/...
```

Then click `Refresh Real Data`. The collector parses available public tables and leaves missing fields as `N/A`.

## Cache

Collected data is cached in:

```text
data/cache/squad_data.sqlite
```

The app loads cached data by default to avoid unnecessary repeated requests. Use `Refresh Real Data` for a manual refresh.

## Data Quality

The `Data Sources & Reliability` page includes:

- collector logs;
- missing field report;
- stale timestamp report;
- incoherence checks;
- player-level provenance.

The `Raw Data Explorer` page includes:

- raw FBref category CSVs from `data/fbref_raw/`;
- cleaned FBref/player merge outputs from `data/processed/`;
- available-column inspection;
- CSV export buttons.

Programmatic checks live in:

```text
morocco_ai_squad/services/data_quality.py
```

## Scoring

Scoring is intentionally conservative. It computes a score only if enough real inputs exist. If not, the score is `N/A`.

Available score inputs:

- recent form;
- league level;
- playing time;
- international experience;
- tactical fit;
- versatility.

Some of these require future real-data providers or curated verified datasets. They are not guessed.

## AI Analysis

The AI module receives only collected/cached fields. It is instructed not to infer missing data. Offline mode also refuses to produce strong football claims when data is insufficient.

Optional OpenAI setup:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
```

## Limitations

- Several requested sources do not provide simple, stable, public player-stat APIs.
- Some websites restrict automated access or require dynamic/session-based loading.
- Player matching across sources requires stable IDs; the seed file currently leaves IDs as `N/A` until manually configured.
- Transfer values, injuries and transfer histories are provider-dependent and often not freely available at scale.
- The project is production-shaped, but real accuracy depends on configured source credentials and identifiers.

## GitHub / LinkedIn Positioning

Good framing:

- "I built a real-data-first football analytics pipeline."
- "The project refuses to invent data and surfaces quality limitations."
- "Collectors are source-aware and legally cautious."
- "The UI combines football analytics, tactical modeling, AI reporting and data engineering."

Avoid claiming complete real coverage until source IDs/API keys are configured and quality reports are clean.

## License

MIT.
