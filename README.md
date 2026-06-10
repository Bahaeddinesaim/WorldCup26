# Morocco World Cup 2026 AI Squad Analyzer

Professional AI and football analytics platform for evaluating Morocco's 2026 World Cup squad pool, comparing players by role, generating tactical lineups and exporting an AI-assisted report.

> Data transparency notice: the repository ships with a seed dataset for demonstration. It clearly separates `real`, `manual` and `estimated` data. Do not present estimated metrics as verified facts. Connect validated providers before publishing factual performance claims.

## Features

- Premium Streamlit dashboard with Morocco-inspired visual identity.
- Squad overview: age, clubs, leagues, line distribution and weighted top players.
- Detailed player profiles with statistical snapshot, strengths, weaknesses and AI analysis.
- Position-by-position comparison for goalkeepers, centre backs, full backs, midfielders, wingers and strikers.
- Weighted scoring model:
  - Recent form: 25%
  - League level: 15%
  - Playing time: 20%
  - International experience: 15%
  - Tactical fit: 15%
  - Versatility: 10%
- Tactical engine for:
  - 4-2-3-1
  - 4-3-3
  - 3-4-3
  - 4-4-2
  - 3-5-2
- Visual football pitch with selected players.
- Formation strengths, weaknesses, tactical risks and recommended substitutes.
- Full AI report generation with PDF export.
- SQLite persistence seeded from CSV.
- Source-provider architecture ready for legal public data or paid API integration.

## Tech Stack

- Python
- Streamlit
- Pandas
- Plotly
- SQLite
- BeautifulSoup / requests scaffolding
- OpenAI API optional
- Gemini-ready configuration
- fpdf2 PDF export

## Project Structure

```text
.
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── LICENSE
├── data/
│   └── seed_players.csv
├── assets/
│   └── screenshots/
└── morocco_ai_squad/
    ├── ai_analysis.py
    ├── charts.py
    ├── config.py
    ├── data_loader.py
    ├── database.py
    ├── report.py
    ├── scoring.py
    ├── tactics.py
    ├── ui.py
    └── sources/
        ├── base.py
        ├── mock_provider.py
        └── public_web_provider.py
```

## Local Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

## Optional AI Configuration

By default, the app runs in offline mode with deterministic football-analysis text.

To use OpenAI:

```env
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

Gemini settings are included in `.env.example` for future extension.

## Data Model

The seed CSV contains the initial Moroccan squad pool requested by the project:

- Goalkeepers
- Defenders
- Midfielders
- Forwards
- Reserves

Each player includes:

- Identity and positions
- Age, club and league placeholders
- Recent minutes, goals, assists and defensive indicators
- Weighted scoring inputs
- Data status
- Source name
- Injury status placeholder
- Strengths, weaknesses and squad role projection

Important fields:

- `data_status=real`: validated data from a reliable provider.
- `data_status=manual`: manually curated project data.
- `data_status=estimated`: placeholder or demonstration metric.

## Adding Real Data Sources

Implement a provider in `morocco_ai_squad/sources/` using `PlayerDataProvider`.

Recommended integrations:

- Paid football APIs with clear terms, such as API-Football.
- Public datasets with explicit reuse permissions.
- Manual CSV refreshes from verified scouting reports.
- Public pages only when terms and robots policies allow collection.

Avoid scraping behind login walls, paywalls or services that forbid automated extraction.

## Scoring Logic

The final score is computed in `morocco_ai_squad/scoring.py`:

```python
final_score =
    recent_form * 0.25
  + league_level * 0.15
  + playing_time_score * 0.20
  + international_experience * 0.15
  + tactical_fit * 0.15
  + versatility * 0.10
```

Every score has a generated explanation in the app.

## Tactical Logic

The tactical engine in `morocco_ai_squad/tactics.py` defines slots for every formation. Each slot has:

- Tactical label
- Pitch coordinates
- Accepted positions

The selector picks the best available player for each slot using:

- Player final score
- Primary-position fit
- Secondary-position fit
- Tactical-fit bonus

## GitHub Publishing Checklist

1. Replace or verify estimated data before making factual claims.
2. Add screenshots to `assets/screenshots/`.
3. Add a short demo GIF or LinkedIn-ready screenshot.
4. Keep `.env` out of Git.
5. Push with a clean commit history.
6. Add repository topics: `football-analytics`, `world-cup-2026`, `streamlit`, `ai`, `data-science`, `morocco`.

## LinkedIn Presentation Angle

Suggested post framing:

- Problem: preparing squad decisions requires fragmented data across many sources.
- Solution: an AI and data platform that centralizes player profiles, scoring and tactical simulation.
- Technical depth: Streamlit, SQLite, Pandas, Plotly, source-provider architecture, PDF reporting and optional LLM analysis.
- Responsible data: every metric is labeled as real, manual or estimated.
- Next step: connect validated live APIs and automate weekly refreshes.

## Roadmap

- API-Football connector.
- Match-by-match trend tables.
- Injury availability confidence score.
- Player similarity search.
- Automated weekly refresh workflow.
- GitHub Actions data validation.
- Multilingual reports in English, French and Arabic.

## License

MIT.
