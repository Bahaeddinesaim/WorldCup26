from __future__ import annotations

import textwrap

import pandas as pd

from .config import load_settings
from .data_loader import ensure_required_columns, safe_get


def offline_player_analysis(row: pd.Series) -> str:
    source = safe_get(row, "data_source")
    reliability = safe_get(row, "reliability", "LOW")
    score = safe_get(row, "final_score")
    if score == "N/A":
        return (
            f"{safe_get(row, 'player_name')} has insufficient verified data for a full AI football profile. "
            f"Known fields: position={safe_get(row, 'primary_position')}, club={safe_get(row, 'club')}, "
            f"league={safe_get(row, 'league')}. Source={source}, reliability={reliability}. "
            "The model will not infer form, weaknesses or tactical superiority without collected evidence."
        )
    return (
        f"{safe_get(row, 'player_name')} profile as a {safe_get(row, 'primary_position')} for Morocco. "
        f"The current real-data model rates him at {score}/100. "
        f"Source={source}; reliability={reliability}; last updated={safe_get(row, 'last_updated')}. "
        f"Available indicators include form={safe_get(row, 'recent_form')}, "
        f"minutes score={safe_get(row, 'playing_time_score')} and league level={safe_get(row, 'league_level')}."
    )


def offline_squad_report(players: pd.DataFrame, formation_summary: dict) -> str:
    players = ensure_required_columns(players)
    scored = players.copy()
    scored["score_numeric"] = pd.to_numeric(scored.get("final_score"), errors="coerce")
    top = scored.dropna(subset=["score_numeric"]).sort_values("score_numeric", ascending=False).head(5)
    top_names = ", ".join(top["player_name"].tolist())
    if not top_names:
        top_names = "N/A - insufficient real data to rank players."
    formation = formation_summary.get("formation", "N/A")
    completeness = round(
        float((~players.astype(str).isin(["N/A", "", "nan"])).mean(numeric_only=False).mean() * 100),
        1,
    )
    return textwrap.dedent(
        f"""
        Morocco World Cup 2026 AI Squad Analyzer - Full Report

        Data notice
        This report uses only collected or manually seeded fields. Missing values remain N/A.
        The system does not invent statistics, form, injuries, market values or tactical conclusions.

        Executive summary
        The current squad pool contains {len(players)} players. Dataset completeness is approximately
        {completeness}%. The model recommends {formation}, but tactical confidence depends on the
        amount of real player data available.

        Rankable players
        {top_names}

        Tactical recommendation
        Strengths: {formation_summary.get('strengths', 'N/A')}
        Weaknesses: {formation_summary.get('weaknesses', 'N/A')}
        Risks: {formation_summary.get('risks', 'N/A')}

        Conclusion
        Conclusion
        If the quality report shows many N/A values, the football conclusion should be treated as
        provisional. Add API keys, FBref URLs or approved source exports, refresh the cache, then
        rerun the report.
        """
    ).strip()


def generate_player_analysis(row: pd.Series) -> str:
    settings = load_settings()
    if settings.ai_provider == "openai" and settings.openai_api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are a concise football analyst."},
                    {
                        "role": "user",
                        "content": (
                            "Write a professional squad profile in English from this data: "
                            f"{row.to_dict()}. Do not infer unavailable fields. Say clearly when data is insufficient."
                        ),
                    },
                ],
                temperature=0.35,
            )
            return response.choices[0].message.content or offline_player_analysis(row)
        except Exception:
            return offline_player_analysis(row)
    return offline_player_analysis(row)


def generate_full_report(players: pd.DataFrame, formation_summary: dict) -> str:
    settings = load_settings()
    base_report = offline_squad_report(players, formation_summary)
    if settings.ai_provider == "openai" and settings.openai_api_key:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": "You are an elite football data analyst."},
                    {
                        "role": "user",
                        "content": (
                            "Rewrite this into a polished executive football report. Do not invent missing data. "
                            "Keep the N/A and data-quality warning explicit:\n\n" + base_report
                        ),
                    },
                ],
                temperature=0.4,
            )
            return response.choices[0].message.content or base_report
        except Exception:
            return base_report
    return base_report
