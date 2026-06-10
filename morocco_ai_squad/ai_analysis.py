from __future__ import annotations

import textwrap

import pandas as pd

from .config import load_settings


def offline_player_analysis(row: pd.Series) -> str:
    status = row.get("data_status", "manual")
    return (
        f"{row['player_name']} profile as a {row['primary_position']} for Morocco. "
        f"The current model rates him at {row['final_score']}/100 using {status} data. "
        f"His strongest indicators are form ({row['recent_form']}/100), playing time "
        f"({row['playing_time_score']}/100) and tactical fit ({row['tactical_fit']}/100). "
        f"Role in squad: {row['role_projection']}."
    )


def offline_squad_report(players: pd.DataFrame, formation_summary: dict) -> str:
    top = players.sort_values("final_score", ascending=False).head(5)
    watched = players.sort_values(["potential", "final_score"], ascending=False).head(5)
    top_names = ", ".join(top["player_name"].tolist())
    watched_names = ", ".join(watched["player_name"].tolist())
    formation = formation_summary["formation"]
    return textwrap.dedent(
        f"""
        Morocco World Cup 2026 AI Squad Analyzer - Full Report

        Data notice
        This report uses a hybrid dataset. Fields marked real can come from validated providers, manual
        fields are curated by the project owner, and estimated fields are model placeholders designed
        for demonstration until API integrations are activated.

        Executive summary
        The current squad pool contains {len(players)} players across goalkeepers, defenders,
        midfielders and forwards. The model recommends {formation} as the leading structure based
        on weighted form, league level, playing time, international experience, tactical fit and versatility.

        Core players
        {top_names}

        Players to monitor
        {watched_names}

        Tactical recommendation
        Strengths: {formation_summary['strengths']}
        Weaknesses: {formation_summary['weaknesses']}
        Risks: {formation_summary['risks']}

        Conclusion
        Morocco's best profile is a balanced team with elite wide quality, a secure goalkeeper,
        and midfielders selected according to game state. The next step is connecting live data
        providers to replace estimated indicators with real match-by-match evidence.
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
                            f"{row.to_dict()}"
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
                            "Rewrite this into a polished executive football report, keeping "
                            "the data-status warning explicit:\n\n" + base_report
                        ),
                    },
                ],
                temperature=0.4,
            )
            return response.choices[0].message.content or base_report
        except Exception:
            return base_report
    return base_report
