from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Slot:
    code: str
    label: str
    x: float
    y: float
    accepted_positions: tuple[str, ...]


FORMATIONS: dict[str, list[Slot]] = {
    "4-2-3-1": [
        Slot("GK", "Goalkeeper", 50, 91, ("GK",)),
        Slot("RB", "Right back", 82, 72, ("RB", "RWB", "LB")),
        Slot("RCB", "Right centre back", 61, 76, ("CB", "RB")),
        Slot("LCB", "Left centre back", 39, 76, ("CB", "LB")),
        Slot("LB", "Left back", 18, 72, ("LB", "LWB", "RB")),
        Slot("RDM", "Right pivot", 60, 57, ("DM", "CM")),
        Slot("LDM", "Left pivot", 40, 57, ("DM", "CM")),
        Slot("RW", "Right winger", 82, 37, ("RW", "LW", "AM")),
        Slot("AM", "Number ten", 50, 35, ("AM", "CM", "RW", "LW")),
        Slot("LW", "Left winger", 18, 37, ("LW", "RW", "AM")),
        Slot("ST", "Striker", 50, 15, ("ST", "CF", "RW", "LW")),
    ],
    "4-3-3": [
        Slot("GK", "Goalkeeper", 50, 91, ("GK",)),
        Slot("RB", "Right back", 82, 72, ("RB", "RWB", "LB")),
        Slot("RCB", "Right centre back", 61, 76, ("CB", "RB")),
        Slot("LCB", "Left centre back", 39, 76, ("CB", "LB")),
        Slot("LB", "Left back", 18, 72, ("LB", "LWB", "RB")),
        Slot("DM", "Holding midfielder", 50, 59, ("DM", "CM")),
        Slot("RCM", "Right eight", 66, 47, ("CM", "AM", "DM")),
        Slot("LCM", "Left eight", 34, 47, ("CM", "AM", "DM")),
        Slot("RW", "Right winger", 82, 28, ("RW", "LW", "AM")),
        Slot("LW", "Left winger", 18, 28, ("LW", "RW", "AM")),
        Slot("ST", "Striker", 50, 16, ("ST", "CF")),
    ],
    "3-4-3": [
        Slot("GK", "Goalkeeper", 50, 91, ("GK",)),
        Slot("RCB", "Right centre back", 70, 75, ("CB", "RB")),
        Slot("CB", "Central centre back", 50, 78, ("CB", "DM")),
        Slot("LCB", "Left centre back", 30, 75, ("CB", "LB")),
        Slot("RWB", "Right wing back", 86, 54, ("RWB", "RB", "RW")),
        Slot("RCM", "Right central mid", 60, 54, ("CM", "DM", "AM")),
        Slot("LCM", "Left central mid", 40, 54, ("CM", "DM", "AM")),
        Slot("LWB", "Left wing back", 14, 54, ("LWB", "LB", "LW")),
        Slot("RW", "Right forward", 78, 26, ("RW", "LW", "AM")),
        Slot("LW", "Left forward", 22, 26, ("LW", "RW", "AM")),
        Slot("ST", "Striker", 50, 15, ("ST", "CF")),
    ],
    "4-4-2": [
        Slot("GK", "Goalkeeper", 50, 91, ("GK",)),
        Slot("RB", "Right back", 82, 72, ("RB", "RWB", "LB")),
        Slot("RCB", "Right centre back", 61, 76, ("CB", "RB")),
        Slot("LCB", "Left centre back", 39, 76, ("CB", "LB")),
        Slot("LB", "Left back", 18, 72, ("LB", "LWB", "RB")),
        Slot("RM", "Right midfielder", 82, 49, ("RW", "RM", "AM", "RB")),
        Slot("RCM", "Right central mid", 59, 52, ("CM", "DM", "AM")),
        Slot("LCM", "Left central mid", 41, 52, ("CM", "DM", "AM")),
        Slot("LM", "Left midfielder", 18, 49, ("LW", "LM", "AM", "LB")),
        Slot("RST", "Right striker", 60, 21, ("ST", "CF", "RW")),
        Slot("LST", "Left striker", 40, 21, ("ST", "CF", "LW")),
    ],
    "3-5-2": [
        Slot("GK", "Goalkeeper", 50, 91, ("GK",)),
        Slot("RCB", "Right centre back", 70, 75, ("CB", "RB")),
        Slot("CB", "Central centre back", 50, 78, ("CB", "DM")),
        Slot("LCB", "Left centre back", 30, 75, ("CB", "LB")),
        Slot("RWB", "Right wing back", 86, 55, ("RWB", "RB", "RW")),
        Slot("DM", "Holding midfielder", 50, 59, ("DM", "CM")),
        Slot("RCM", "Right eight", 64, 45, ("CM", "AM", "DM")),
        Slot("LCM", "Left eight", 36, 45, ("CM", "AM", "DM")),
        Slot("LWB", "Left wing back", 14, 55, ("LWB", "LB", "LW")),
        Slot("RST", "Right striker", 60, 20, ("ST", "CF", "RW")),
        Slot("LST", "Left striker", 40, 20, ("ST", "CF", "LW")),
    ],
}


FORMATION_NOTES = {
    "4-2-3-1": {
        "strengths": "Structure stable, double pivot protecteur, bonne liberte entre les lignes pour le createur.",
        "weaknesses": "Peut isoler le neuf si les ailiers restent trop larges.",
        "risks": "Dependance forte a la qualite de sortie des lateraux sous pression.",
    },
    "4-3-3": {
        "strengths": "Pressing naturel, largeur claire, bons relais pour controler le tempo.",
        "weaknesses": "Exige des interieurs capables de couvrir beaucoup de terrain.",
        "risks": "Transitions defensives exposees si les ailiers perdent vite le ballon.",
    },
    "3-4-3": {
        "strengths": "Sortie a trois, haute densite dans les couloirs, bon cadre pour les pistons.",
        "weaknesses": "Moins de presence axiale au milieu contre un 4-3-3 agressif.",
        "risks": "Les pistons doivent tenir volume, discipline et qualite de centres.",
    },
    "4-4-2": {
        "strengths": "Lecture simple, deux attaquants proches, bloc median compact.",
        "weaknesses": "Peut manquer d'un joueur entre les lignes.",
        "risks": "Inferiorite numerique au milieu contre les equipes a trois centraux.",
    },
    "3-5-2": {
        "strengths": "Densite axiale, deux pointes pour attaquer la surface, couverture defensive large.",
        "weaknesses": "Moins d'ailiers naturels dans les trente derniers metres.",
        "risks": "Creation dependante des pistons et des courses des interieurs.",
    },
}


def _candidate_positions(row: pd.Series) -> set[str]:
    return {row["primary_position"], *str(row["secondary_positions"]).split("|")}


def _slot_score(row: pd.Series, slot: Slot) -> float:
    positions = _candidate_positions(row)
    if row["primary_position"] in slot.accepted_positions:
        fit_bonus = 9
    elif positions.intersection(slot.accepted_positions):
        fit_bonus = 4
    else:
        fit_bonus = -25
    return float(row["final_score"]) + fit_bonus + float(row["tactical_fit"]) * 0.04


def build_lineup(players: pd.DataFrame, formation: str) -> dict:
    available = players.copy().sort_values("final_score", ascending=False)
    selected_ids: set[str] = set()
    lineup = []

    for slot in FORMATIONS[formation]:
        candidates = available[~available["player_id"].isin(selected_ids)].copy()
        candidates["slot_score"] = candidates.apply(lambda row: _slot_score(row, slot), axis=1)
        chosen = candidates.sort_values("slot_score", ascending=False).iloc[0]
        selected_ids.add(chosen["player_id"])
        lineup.append(
            {
                "slot": slot,
                "player": chosen.to_dict(),
                "reason": _selection_reason(chosen, slot),
            }
        )

    substitutes = (
        players[~players["player_id"].isin(selected_ids)]
        .sort_values("final_score", ascending=False)
        .head(7)
        .to_dict("records")
    )
    notes = FORMATION_NOTES[formation]
    return {"formation": formation, "lineup": lineup, "substitutes": substitutes, **notes}


def _selection_reason(player: pd.Series, slot: Slot) -> str:
    return (
        f"{player['player_name']} est choisi comme {slot.label.lower()} grace a un score de "
        f"{player['final_score']}/100, un fit tactique de {player['tactical_fit']}/100 "
        f"et un profil compatible avec {slot.code}."
    )


def recommended_formation(players: pd.DataFrame) -> str:
    scores = {}
    for formation in FORMATIONS:
        lineup = build_lineup(players, formation)["lineup"]
        scores[formation] = sum(item["player"]["final_score"] for item in lineup) / len(lineup)
    return max(scores, key=scores.get)
