from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


COLORWAY = ["#c1121f", "#006b3f", "#f5c542", "#ffffff", "#222222"]


def line_distribution(players: pd.DataFrame) -> go.Figure:
    fig = px.pie(
        players,
        names="line",
        hole=0.55,
        color_discrete_sequence=COLORWAY,
    )
    fig.update_layout(showlegend=True, margin=dict(l=10, r=10, t=20, b=10), height=310)
    return fig


def score_bar(players: pd.DataFrame, n: int = 12) -> go.Figure:
    data = players.copy()
    data["score_numeric"] = pd.to_numeric(data["final_score"], errors="coerce")
    data = data.dropna(subset=["score_numeric"]).sort_values("score_numeric", ascending=False).head(n)
    if data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No reliable real-data score available yet", showarrow=False)
        fig.update_layout(height=430, margin=dict(l=10, r=10, t=20, b=10))
        return fig
    fig = px.bar(
        data,
        x="score_numeric",
        y="player_name",
        orientation="h",
        color="line",
        color_discrete_sequence=COLORWAY,
        text="final_score",
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_title="Score",
        yaxis_title="",
        height=430,
        margin=dict(l=10, r=10, t=20, b=10),
    )
    return fig


def radar_player(row: pd.Series) -> go.Figure:
    categories = [
        "recent_form",
        "league_level",
        "playing_time_score",
        "international_experience",
        "tactical_fit",
        "versatility",
    ]
    values = [pd.to_numeric(row.get(c), errors="coerce") for c in categories]
    values = [0 if pd.isna(v) else float(v) for v in values]
    labels = ["Form", "League", "Minutes", "Experience", "Tactical fit", "Versatility"]
    fig = go.Figure(
        data=[
            go.Scatterpolar(
                r=values + [values[0]],
                theta=labels + [labels[0]],
                fill="toself",
                line_color="#c1121f",
            )
        ]
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
        height=360,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def group_comparison(players: pd.DataFrame) -> go.Figure:
    players = players.copy()
    players["score_numeric"] = pd.to_numeric(players["final_score"], errors="coerce")
    if players["score_numeric"].dropna().empty:
        fig = go.Figure()
        fig.add_annotation(text="No reliable group scores available yet", showarrow=False)
        fig.update_layout(height=340, margin=dict(l=10, r=10, t=20, b=20))
        return fig
    grouped = (
        players.groupby("position_group", as_index=False)["score_numeric"]
        .mean()
        .sort_values("score_numeric", ascending=False)
    )
    fig = px.bar(
        grouped,
        x="position_group",
        y="score_numeric",
        color="position_group",
        color_discrete_sequence=COLORWAY,
        text=grouped["score_numeric"].round(1),
    )
    fig.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="Average score",
        height=340,
        margin=dict(l=10, r=10, t=20, b=20),
    )
    return fig
