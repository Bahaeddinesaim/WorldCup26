from __future__ import annotations

import streamlit as st

from morocco_ai_squad.ai_analysis import generate_full_report, generate_player_analysis
from morocco_ai_squad.charts import group_comparison, line_distribution, radar_player, score_bar
from morocco_ai_squad.data_loader import ensure_database_seeded, filter_players
from morocco_ai_squad.report import build_pdf
from morocco_ai_squad.scoring import POSITION_GROUPS, add_position_groups, add_scores, compare_by_group
from morocco_ai_squad.tactics import FORMATIONS, build_lineup, recommended_formation
from morocco_ai_squad.ui import data_notice, hero, inject_theme, lineup_table, metric_card, player_cards, render_pitch


st.set_page_config(
    page_title="Morocco WC 2026 AI Squad Analyzer",
    page_icon="MA",
    layout="wide",
)

inject_theme()

players = ensure_database_seeded()
players = add_position_groups(add_scores(players))

with st.sidebar:
    st.title("Squad Controls")
    search = st.text_input("Search player or club")
    lines = st.multiselect("Lines", sorted(players["line"].unique().tolist()))
    source_types = st.multiselect("Data status", sorted(players["data_status"].unique().tolist()))
    formation = st.selectbox("Formation", list(FORMATIONS.keys()), index=list(FORMATIONS.keys()).index("4-2-3-1"))
    st.caption("Seed data is designed for the app. Connect real providers before making factual claims.")

filtered = filter_players(players, search, lines, source_types)

hero()
data_notice()

tabs = st.tabs(["Dashboard", "Players", "Comparisons", "Tactics", "AI Report", "Data Sources"])

with tabs[0]:
    avg_age = filtered["age"].mean() if len(filtered) else 0
    avg_score = filtered["final_score"].mean() if len(filtered) else 0
    clubs = filtered["club"].nunique() if len(filtered) else 0
    leagues = filtered["league"].nunique() if len(filtered) else 0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        metric_card("Players", str(len(filtered)), "Current filtered squad pool")
    with m2:
        metric_card("Average age", f"{avg_age:.1f}", "Years")
    with m3:
        metric_card("Average score", f"{avg_score:.1f}", "Weighted model score")
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
    selected_name = st.selectbox("Select player", filtered["player_name"].sort_values().tolist())
    selected = filtered[filtered["player_name"] == selected_name].iloc[0]

    c1, c2 = st.columns([0.42, 0.58])
    with c1:
        st.plotly_chart(radar_player(selected), use_container_width=True)
    with c2:
        metric_card(selected["player_name"], f"{selected['final_score']}/100", selected["role_projection"])
        st.write(
            {
                "Position": selected["primary_position"],
                "Secondary positions": selected["secondary_positions"],
                "Age": int(selected["age"]),
                "Club": selected["club"],
                "League": selected["league"],
                "Data status": selected["data_status"],
                "Injury status": selected["injury_status"],
            }
        )
        st.markdown("**Strengths**")
        st.write(selected["strong_points"])
        st.markdown("**Weaknesses**")
        st.write(selected["weak_points"])
        st.markdown("**AI profile**")
        st.write(generate_player_analysis(selected))

    st.subheader("Recent statistical snapshot")
    st.dataframe(
        filtered[
            [
                "player_name",
                "minutes_recent",
                "goals_recent",
                "assists_recent",
                "clean_sheets_recent",
                "duels_won_pct",
                "pass_success_pct",
                "avg_rating",
                "final_score",
                "data_status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with tabs[2]:
    st.subheader("Position-by-position comparison")
    st.plotly_chart(group_comparison(filtered), use_container_width=True)
    group = st.selectbox("Position group", list(POSITION_GROUPS.keys()))
    comparison = compare_by_group(filtered, group)
    st.dataframe(
        comparison[
            [
                "player_name",
                "primary_position",
                "club",
                "recent_form",
                "league_level",
                "playing_time_score",
                "international_experience",
                "tactical_fit",
                "versatility",
                "final_score",
                "score_explanation",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

with tabs[3]:
    st.subheader(f"Tactical engine - {formation}")
    lineup = build_lineup(filtered, formation)
    pitch_col, detail_col = st.columns([0.48, 0.52])
    with pitch_col:
        render_pitch(lineup)
    with detail_col:
        st.markdown("**Strengths**")
        st.write(lineup["strengths"])
        st.markdown("**Weaknesses**")
        st.write(lineup["weaknesses"])
        st.markdown("**Risks**")
        st.write(lineup["risks"])
        st.dataframe(lineup_table(lineup), use_container_width=True, hide_index=True)
        st.markdown("**Recommended substitutes**")
        st.write(", ".join([p["player_name"] for p in lineup["substitutes"]]))

    st.subheader("All formations")
    cols = st.columns(len(FORMATIONS))
    rec = recommended_formation(filtered)
    for idx, name in enumerate(FORMATIONS):
        built = build_lineup(filtered, name)
        avg = sum(item["player"]["final_score"] for item in built["lineup"]) / 11
        with cols[idx]:
            metric_card(name, f"{avg:.1f}", "Recommended" if name == rec else "Alternative")

with tabs[4]:
    st.subheader("Generate Full AI Report")
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
    st.subheader("Data architecture and source readiness")
    st.write(
        "The app currently ships with a curated seed dataset and a source-provider interface. "
        "Real integrations can be added through `morocco_ai_squad/sources` while preserving data_status."
    )
    st.dataframe(
        players[
            [
                "player_name",
                "club",
                "league",
                "data_status",
                "source_name",
                "injury_status",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
