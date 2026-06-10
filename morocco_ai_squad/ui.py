from __future__ import annotations

import html

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --morocco-red: #b80f1f;
            --morocco-green: #006b3f;
            --morocco-gold: #d8a928;
            --ink: #171717;
            --muted: #69707a;
            --panel: #ffffff;
            --soft: #f7f5ef;
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(184,15,31,.12), transparent 28rem),
                linear-gradient(180deg, #fffaf2 0%, #f7f8f5 38%, #ffffff 100%);
            color: var(--ink);
        }
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 3rem;
            max-width: 1320px;
        }
        [data-testid="stSidebar"] {
            background: #101713;
        }
        [data-testid="stSidebar"] * {
            color: #f7f5ef;
        }
        .hero {
            min-height: 280px;
            border-radius: 0;
            padding: 38px 36px;
            background:
                linear-gradient(120deg, rgba(13,32,24,.94), rgba(184,15,31,.86)),
                url("https://images.unsplash.com/photo-1518091043644-c1d4457512c6?auto=format&fit=crop&w=1600&q=80");
            background-size: cover;
            background-position: center;
            color: white;
            box-shadow: 0 24px 70px rgba(47, 28, 19, .20);
        }
        .hero h1 {
            font-size: clamp(2.1rem, 5vw, 4.7rem);
            line-height: 1;
            letter-spacing: 0;
            margin: 0 0 14px 0;
            max-width: 940px;
        }
        .hero p {
            max-width: 780px;
            color: rgba(255,255,255,.90);
            font-size: 1.05rem;
            margin: 0;
        }
        .data-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 6px 10px;
            border: 1px solid rgba(255,255,255,.28);
            color: #fff;
            background: rgba(0,0,0,.18);
            font-size: .82rem;
            margin-bottom: 18px;
        }
        .metric-card {
            background: rgba(255,255,255,.88);
            border: 1px solid rgba(23,23,23,.08);
            border-top: 3px solid var(--morocco-red);
            padding: 18px;
            min-height: 112px;
            box-shadow: 0 14px 32px rgba(16, 23, 19, .08);
        }
        .metric-card span {
            color: var(--muted);
            font-size: .82rem;
            text-transform: uppercase;
            letter-spacing: .08em;
        }
        .metric-card strong {
            display: block;
            margin-top: 8px;
            font-size: 1.85rem;
            line-height: 1.1;
        }
        .player-card {
            background: var(--panel);
            border: 1px solid rgba(23,23,23,.08);
            border-left: 4px solid var(--morocco-green);
            padding: 16px;
            min-height: 178px;
            box-shadow: 0 12px 28px rgba(16, 23, 19, .07);
        }
        .player-card h3 {
            margin: 0 0 6px 0;
            font-size: 1.05rem;
        }
        .player-card p {
            color: var(--muted);
            margin: 2px 0;
            font-size: .9rem;
        }
        .pill {
            display: inline-block;
            padding: 4px 8px;
            margin: 6px 5px 0 0;
            background: #f2ead8;
            color: #3b321d;
            font-size: .76rem;
            border: 1px solid rgba(216,169,40,.32);
        }
        .notice {
            background: #fff6df;
            border-left: 4px solid var(--morocco-gold);
            padding: 13px 15px;
            color: #423615;
            margin: 16px 0;
        }
        .pitch {
            position: relative;
            width: 100%;
            aspect-ratio: 0.72 / 1;
            min-height: 620px;
            background:
                linear-gradient(90deg, rgba(255,255,255,.08) 49.5%, rgba(255,255,255,.35) 50%, rgba(255,255,255,.08) 50.5%),
                repeating-linear-gradient(0deg, #136c45 0 72px, #0d5d3a 72px 144px);
            border: 3px solid rgba(255,255,255,.86);
            box-shadow: inset 0 0 0 2px rgba(255,255,255,.18), 0 22px 54px rgba(0,0,0,.14);
            overflow: hidden;
        }
        .pitch:before {
            content: "";
            position: absolute;
            inset: 5%;
            border: 2px solid rgba(255,255,255,.55);
        }
        .pitch:after {
            content: "";
            position: absolute;
            left: 33%;
            top: 43%;
            width: 34%;
            aspect-ratio: 1;
            border: 2px solid rgba(255,255,255,.55);
            border-radius: 50%;
        }
        .player-dot {
            position: absolute;
            width: 124px;
            min-height: 58px;
            transform: translate(-50%, -50%);
            background: rgba(255,255,255,.94);
            border: 2px solid #d8a928;
            color: #101713;
            text-align: center;
            padding: 8px 7px;
            box-shadow: 0 10px 22px rgba(0,0,0,.22);
            z-index: 2;
        }
        .player-dot strong {
            display: block;
            font-size: .78rem;
            line-height: 1.15;
        }
        .player-dot span {
            display: block;
            color: #b80f1f;
            font-size: .7rem;
            margin-top: 2px;
        }
        @media (max-width: 760px) {
            .hero { padding: 28px 22px; }
            .pitch { min-height: 540px; }
            .player-dot { width: 96px; font-size: .72rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="data-badge">Hybrid data engine - manual, estimated and API-ready</div>
            <h1>Morocco World Cup 2026 AI Squad Analyzer</h1>
            <p>Professional football analytics platform for squad evaluation, tactical selection,
            AI-generated reporting and data-source transparency.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, caption: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <span>{html.escape(label)}</span>
            <strong>{html.escape(value)}</strong>
            <small>{html.escape(caption)}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


def data_notice() -> None:
    st.markdown(
        """
        <div class="notice">
        Real-data mode: unavailable values stay <b>N/A</b>. The app never fabricates metrics.
        Every collected field carries a source, update date and reliability level.
        </div>
        """,
        unsafe_allow_html=True,
    )


def player_cards(players: pd.DataFrame, limit: int = 6) -> None:
    rows = players.sort_values("final_score", ascending=False).head(limit).to_dict("records")
    cols = st.columns(3)
    for idx, row in enumerate(rows):
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div class="player-card">
                    <h3>{html.escape(row['player_name'])}</h3>
                    <p>{html.escape(row['primary_position'])} - {html.escape(row['club'])}</p>
                    <p>{html.escape(row['league'])}</p>
                    <span class="pill">Score {row.get('final_score', 'N/A')}/100</span>
                    <span class="pill">{html.escape(str(row.get('reliability', 'LOW')))}</span>
                    <p style="margin-top:10px;">Source: {html.escape(str(row.get('data_source', 'N/A')))}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_pitch(lineup: dict) -> None:
    dots = []
    for item in lineup["lineup"]:
        slot = item["slot"]
        player = item["player"]
        name = html.escape(player["short_name"])
        score = html.escape(str(player["final_score"]))
        dots.append(
            f'<div class="player-dot" style="left:{slot.x}%; top:{slot.y}%;">'
            f"<strong>{name}</strong>"
            f"<span>{html.escape(slot.code)} - {score}</span>"
            "</div>"
        )

    pitch_html = f"""
    <!doctype html>
    <html>
    <head>
    <style>
    html, body {{
        margin: 0;
        padding: 0;
        background: transparent;
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    .pitch {{
        position: relative;
        width: 100%;
        height: 680px;
        background:
            linear-gradient(90deg, rgba(255,255,255,.08) 49.5%, rgba(255,255,255,.35) 50%, rgba(255,255,255,.08) 50.5%),
            repeating-linear-gradient(0deg, #136c45 0 72px, #0d5d3a 72px 144px);
        border: 3px solid rgba(255,255,255,.86);
        box-sizing: border-box;
        box-shadow: inset 0 0 0 2px rgba(255,255,255,.18), 0 22px 54px rgba(0,0,0,.14);
        overflow: hidden;
    }}
    .pitch:before {{
        content: "";
        position: absolute;
        inset: 5%;
        border: 2px solid rgba(255,255,255,.55);
    }}
    .pitch:after {{
        content: "";
        position: absolute;
        left: 33%;
        top: 43%;
        width: 34%;
        aspect-ratio: 1;
        border: 2px solid rgba(255,255,255,.55);
        border-radius: 50%;
    }}
    .box-top, .box-bottom {{
        position: absolute;
        left: 27%;
        width: 46%;
        height: 15%;
        border: 2px solid rgba(255,255,255,.55);
        z-index: 1;
    }}
    .box-top {{ top: 5%; border-top: 0; }}
    .box-bottom {{ bottom: 5%; border-bottom: 0; }}
    .player-dot {{
        position: absolute;
        width: 122px;
        min-height: 58px;
        transform: translate(-50%, -50%);
        background: rgba(255,255,255,.96);
        border: 2px solid #d8a928;
        color: #101713;
        text-align: center;
        padding: 8px 7px;
        box-shadow: 0 10px 22px rgba(0,0,0,.22);
        z-index: 3;
        box-sizing: border-box;
    }}
    .player-dot strong {{
        display: block;
        font-size: 12px;
        line-height: 1.15;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}
    .player-dot span {{
        display: block;
        color: #b80f1f;
        font-size: 11px;
        margin-top: 3px;
    }}
    @media (max-width: 520px) {{
        .pitch {{ height: 600px; }}
        .player-dot {{ width: 94px; min-height: 52px; padding: 7px 5px; }}
        .player-dot strong {{ font-size: 10px; }}
        .player-dot span {{ font-size: 9px; }}
    }}
    </style>
    </head>
    <body>
        <div class="pitch">
            <div class="box-top"></div>
            <div class="box-bottom"></div>
            {''.join(dots)}
        </div>
    </body>
    </html>
    """
    components.html(pitch_html, height=700, scrolling=False)


def lineup_table(lineup: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Position": item["slot"].code,
                "Role": item["slot"].label,
                "Player": item["player"]["player_name"],
                "Score": item["player"]["final_score"],
                "Reason": item["reason"],
            }
            for item in lineup["lineup"]
        ]
    )
