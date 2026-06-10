from __future__ import annotations

import pandas as pd
import streamlit as st

from morocco_ai_squad.config import FBREF_RAW_DIR, PROCESSED_DIR
from morocco_ai_squad.ai_analysis import generate_full_report, generate_player_analysis
from morocco_ai_squad.charts import group_comparison, line_distribution, radar_player, score_bar
from morocco_ai_squad.data_loader import ensure_real_data_loaded, ensure_required_columns, filter_players, refresh_real_pipeline, safe_get
from morocco_ai_squad.database.db import load_fetch_logs
from morocco_ai_squad.report import build_pdf
from morocco_ai_squad.scoring import POSITION_GROUPS, add_position_groups, add_scores, compare_by_group
from morocco_ai_squad.services.data_quality import (
    completeness_by_player,
    duplicate_report,
    incoherence_report,
    missing_value_report,
    quality_summary,
    source_availability_report,
    stale_data_report,
)
from morocco_ai_squad.tactics import FORMATIONS, build_lineup, recommended_formation
from morocco_ai_squad.ui import data_notice, hero, inject_theme, lineup_table, metric_card, player_cards, render_pitch


st.set_page_config(
    page_title="Morocco WC 2026 AI Squad Analyzer",
    page_icon="MA",
    layout="wide",
)

inject_theme()

players = ensure_required_columns(ensure_real_data_loaded())
players = ensure_required_columns(add_position_groups(add_scores(players)))


def safe_table(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    data = ensure_required_columns(df)
    for column in columns:
        if column not in data.columns:
            data[column] = "N/A"
    return data[columns]


def read_csv_files(folder) -> dict[str, pd.DataFrame]:
    files = {}
    if folder.exists():
        for path in sorted(folder.glob("*.csv")):
            try:
                files[path.name] = pd.read_csv(path)
            except Exception:
                files[path.name] = pd.DataFrame({"error": [f"Could not read {path.name}"]})
    return files

with st.sidebar:
    st.title("Squad Controls")
    if st.button("Refresh Real Data", use_container_width=True):
        with st.spinner("Collecting real data from configured sources..."):
            players, logs = refresh_real_pipeline()
            players = ensure_required_columns(add_position_groups(add_scores(players)))
            st.success(f"Refresh complete. Collector events: {len(logs)}")
    search = st.text_input("Search player or club")
    lines = st.multiselect("Lines", sorted(players["line"].dropna().astype(str).unique().tolist()))
    source_types = st.multiselect("Reliability", sorted(players["reliability"].dropna().astype(str).unique().tolist()))
    formation = st.selectbox("Formation", list(FORMATIONS.keys()), index=list(FORMATIONS.keys()).index("4-2-3-1"))
    st.caption("Unavailable values remain N/A. Add API keys or approved URLs, then refresh.")

filtered = ensure_required_columns(filter_players(players, search, lines, source_types))

hero()
data_notice()

tabs = st.tabs([
    "Dashboard",
    "Players",
    "Comparisons",
    "Tactical Analysis",
    "AI Report",
    "Raw Data Explorer",
    "Data Quality",
    "Data Sources & Reliability",
])

with tabs[0]:
    age_numeric = pd.to_numeric(filtered["age"], errors="coerce")
    score_numeric = pd.to_numeric(filtered["final_score"], errors="coerce")
    avg_age = age_numeric.mean() if len(filtered) and not age_numeric.dropna().empty else None
    avg_score = score_numeric.mean() if len(filtered) and not score_numeric.dropna().empty else None
    clubs = filtered["club"].nunique() if len(filtered) else 0
    leagues = filtered["league"].nunique() if len(filtered) else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("Players", str(len(filtered)), "Current filtered squad pool")
    with m2:
        metric_card("Average age", f"{avg_age:.1f}" if avg_age is not None else "N/A", "Years")
    with m3:
        metric_card("Average score", f"{avg_score:.1f}" if avg_score is not None else "N/A", "Real-data weighted score")
    with m4:
        metric_card("Clubs / leagues", f"{clubs} / {leagues}", "Representation")

    left, right = st.columns([0.42, 0.58])
    with left:
        st.subheader("Squad distribution")
        st.plotly_chart(line_distribution(filtered), use_container_width=True)
    with right:
        st.subheader("Top weighted profiles")
        st.plotly_chart(score_bar(filtered), use_container_width=True)

    st.subheader("Premium player cards")
    player_cards(filtered, limit=6)

with tabs[1]:
    st.subheader("Detailed player profile")
    if filtered.empty:
        st.warning("No player matches the current filters.")
    else:
        selected_name = st.selectbox("Select player", filtered["player_name"].sort_values().tolist())
        selected = filtered[filtered["player_name"] == selected_name].iloc[0]

        c1, c2 = st.columns([0.42, 0.58])
        with c1:
            st.plotly_chart(radar_player(selected), use_container_width=True)
        with c2:
            metric_card(
                str(safe_get(selected, "player_name")),
                f"{safe_get(selected, 'final_score')}/100",
                str(safe_get(selected, "role_projection")),
            )
            st.json(
                {
                    "Position": safe_get(selected, "primary_position"),
                    "Secondary positions": safe_get(selected, "secondary_positions"),
                    "Age": safe_get(selected, "age"),
                    "Club": safe_get(selected, "club"),
                    "League": safe_get(selected, "league"),
                    "Data source": safe_get(selected, "data_source"),
                    "Reliability": safe_get(selected, "reliability"),
                    "Last updated": safe_get(selected, "last_updated"),
                    "Injury status": safe_get(selected, "injury_status"),
                }
            )
            st.markdown("**AI profile**")
            st.write(generate_player_analysis(selected))

    st.subheader("Recent statistical snapshot")
    st.dataframe(
        safe_table(
            filtered,
            [
                "player_name",
                "matches_played",
                "minutes_played",
                "goals",
                "assists",
                "clean_sheets",
                "xg",
                "xa",
                "avg_rating",
                "market_value",
                "player_status",
                "final_score",
                "data_source",
                "reliability",
                "last_updated",
            ],
        ),
        use_container_width=True,
        hide_index=True,
    )

with tabs[2]:
    st.subheader("Position-by-position comparison")
    st.plotly_chart(group_comparison(filtered), use_container_width=True)
    group = st.selectbox("Position group", list(POSITION_GROUPS.keys()))
    comparison = ensure_required_columns(compare_by_group(filtered, group))
    st.dataframe(
        safe_table(
            comparison,
            [
                "player_name",
                "primary_position",
                "club",
                "league",
                "recent_form",
                "league_level",
                "playing_time_score",
                "international_experience",
                "tactical_fit",
                "versatility",
                "final_score",
                "data_source",
                "reliability",
                "score_explanation",
            ],
        ),
        use_container_width=True,
        hide_index=True,
    )

with tabs[3]:
    st.subheader(f"Tactical engine - {formation}")
    st.caption("Lineups and recommendations are based only on available collected fields. Missing stats remain N/A.")
    st.dataframe(
        safe_table(
            filtered,
            ["player_name", "line", "primary_position", "club", "league", "minutes_played", "goals", "assists", "final_score", "score_explanation"],
        ),
        use_container_width=True,
        hide_index=True,
    )
    if filtered.empty:
        st.warning("No players available for tactical selection with the current filters.")
    else:
        lineup = build_lineup(filtered, formation)
        pitch_col, detail_col = st.columns([0.48, 0.52])
        with pitch_col:
            render_pitch(lineup)
        with detail_col:
            st.markdown("**Strengths**")
            st.write(safe_get(lineup, "strengths"))
            st.markdown("**Weaknesses**")
            st.write(safe_get(lineup, "weaknesses"))
            st.markdown("**Risks**")
            st.write(safe_get(lineup, "risks"))
            st.dataframe(lineup_table(lineup), use_container_width=True, hide_index=True)
            st.markdown("**Recommended substitutes**")
            substitutes = [str(safe_get(p, "player_name")) for p in safe_get(lineup, "substitutes", [])]
            st.write(", ".join(substitutes) if substitutes else "N/A")

    st.subheader("All formations")
    cols = st.columns(len(FORMATIONS))
    rec = recommended_formation(filtered)
    for idx, name in enumerate(FORMATIONS):
        built = build_lineup(filtered, name)
        numeric = [pd.to_numeric(item["player"].get("final_score"), errors="coerce") for item in built["lineup"]]
        valid = [float(v) for v in numeric if not pd.isna(v)]
        avg = sum(valid) / len(valid) if valid else None
        with cols[idx]:
            metric_card(name, f"{avg:.1f}" if avg is not None else "N/A", "Recommended" if name == rec else "Alternative")

with tabs[4]:
    st.subheader("Generate Full AI Report")
    if filtered.empty:
        st.warning("No players available for report generation with the current filters.")
    else:
        selected_lineup = build_lineup(filtered, recommended_formation(filtered))
        report_text = generate_full_report(filtered, selected_lineup)
        st.text_area("Generated report", report_text, height=460)
        pdf_bytes = build_pdf(report_text)
        st.download_button(
            "Download PDF report",
            data=pdf_bytes,
            file_name="morocco_wc2026_ai_squad_report.pdf",
            mime="application/pdf",
        )

with tabs[5]:
    st.subheader("Raw Data Explorer")
    raw_files = read_csv_files(FBREF_RAW_DIR)
    processed_files = read_csv_files(PROCESSED_DIR)
    if not raw_files and not processed_files:
        st.info("No FBref raw/processed CSV files yet. Click Refresh Real Data to run the scraper.")
    raw_tab, clean_tab, columns_tab = st.tabs(["FBref raw tables", "Cleaned data", "Columns"])
    with raw_tab:
        if raw_files:
            selected_raw = st.selectbox("FBref raw CSV", list(raw_files.keys()))
            raw_df = raw_files[selected_raw]
            st.dataframe(raw_df, use_container_width=True)
            st.download_button(
                "Export raw CSV",
                raw_df.to_csv(index=False).encode("utf-8"),
                file_name=selected_raw,
                mime="text/csv",
            )
        else:
            st.warning("No raw FBref tables saved yet.")
    with clean_tab:
        if processed_files:
            selected_clean = st.selectbox("Processed CSV", list(processed_files.keys()))
            clean_df = processed_files[selected_clean]
            st.dataframe(clean_df, use_container_width=True)
            st.download_button(
                "Export cleaned CSV",
                clean_df.to_csv(index=False).encode("utf-8"),
                file_name=selected_clean,
                mime="text/csv",
            )
        else:
            st.warning("No processed FBref dataset saved yet.")
    with columns_tab:
        all_columns = []
        for name, frame in {**raw_files, **processed_files}.items():
            all_columns.extend([{"file": name, "column": col} for col in frame.columns])
        st.dataframe(pd.DataFrame(all_columns), use_container_width=True, hide_index=True)

with tabs[6]:
    st.subheader("Data Quality")
    summary = quality_summary(players)
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        metric_card("Players", str(summary["players"]), "Seeded squad pool")
    with q2:
        metric_card("Completeness", f"{summary['metric_completeness_pct']}%", "Metric fields filled")
    with q3:
        metric_card("Real rows", str(summary["real_data_rows"]), "Rows enriched by collectors")
    with q4:
        metric_card("Seed only", str(summary["seed_only_rows"]), "Need source IDs/API")

    st.markdown("**Missing fields**")
    st.dataframe(missing_value_report(players), use_container_width=True, hide_index=True)
    st.markdown("**Duplicates**")
    duplicates = duplicate_report(players)
    st.dataframe(duplicates if not duplicates.empty else [{"status": "No duplicates detected"}], use_container_width=True)
    st.markdown("**Stale data**")
    stale = stale_data_report(players)
    st.dataframe(stale if not stale.empty else [{"status": "No stale rows detected"}], use_container_width=True)
    st.markdown("**Sources available**")
    st.dataframe(source_availability_report(players), use_container_width=True, hide_index=True)
    st.markdown("**Completeness by player**")
    st.dataframe(completeness_by_player(players), use_container_width=True, hide_index=True)
    st.markdown("**Incoherence report**")
    incoherent = incoherence_report(players)
    st.dataframe(incoherent if not incoherent.empty else [{"status": "No incoherence detected"}], use_container_width=True)

with tabs[7]:
    st.subheader("Data Sources & Reliability")
    summary = quality_summary(players)
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        metric_card("Players", str(summary["players"]), "Seeded squad pool")
    with q2:
        metric_card("Completeness", f"{summary['metric_completeness_pct']}%", "Metric fields filled")
    with q3:
        metric_card("Real rows", str(summary["real_data_rows"]), "Rows enriched by collectors")
    with q4:
        metric_card("Seed only", str(summary["seed_only_rows"]), "Need source IDs/API")

    st.write(
        "The pipeline prioritizes official/allowed APIs. Scraping collectors run only when explicit URLs "
        "or compliant access are configured. Missing data stays N/A."
    )
    st.markdown("**Configured collectors**")
    st.dataframe(load_fetch_logs(), use_container_width=True, hide_index=True)

    st.markdown("**Missing data report**")
    st.dataframe(missing_value_report(players), use_container_width=True, hide_index=True)

    st.markdown("**Stale data report**")
    stale = stale_data_report(players)
    st.dataframe(stale if not stale.empty else [{"status": "No stale rows detected"}], use_container_width=True)

    st.markdown("**Incoherence report**")
    incoherent = incoherence_report(players)
    st.dataframe(incoherent if not incoherent.empty else [{"status": "No incoherence detected"}], use_container_width=True)

    st.markdown("**Player provenance**")
    st.dataframe(
        safe_table(
            players,
            [
                "player_name",
                "club",
                "league",
                "data_source",
                "source_url",
                "last_updated",
                "reliability",
                "collection_status",
                "market_value",
                "player_status",
                "injury_status",
            ],
        ),
        use_container_width=True,
        hide_index=True,
    )
