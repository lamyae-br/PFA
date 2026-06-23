"""
routes/nations.py — Comparaison entre toutes les nations
"""

from fastapi import APIRouter, Query
from typing import Optional
from schemas import NationsResponse, NationStats
from data_loader import get_players

router = APIRouter()


@router.get("/nations", response_model=NationsResponse)
def compare_nations(
    top: int = Query(20, description="Nombre max de nations à retourner"),
    min_players: int = Query(11, description="Minimum de joueurs par nation")
):
    """
    Top N nations par score PFA moyen.
    Inclut TOUTES les nations avec assez de joueurs.
    """
    df_players = get_players()

    if "nationality_name" not in df_players.columns:
        return NationsResponse(nations=[])

    # Grouper par nationalité
    grouped = df_players.groupby("nationality_name").agg(
        players_count=("short_name", "count"),
        pfa_avg=("pfa_score", "mean"),
        pfa_max=("pfa_score", "max"),
        overall_avg=("overall_raw", "mean")
    ).reset_index()

    # Filtrer les nations avec assez de joueurs
    grouped = grouped[grouped["players_count"] >= min_players]

    # Trier par score PFA moyen
    grouped = grouped.nlargest(top, "pfa_avg")

    result = [
        NationStats(
            nation=str(row["nationality_name"]),
            players_count=int(row["players_count"]),
            pfa_avg=round(float(row["pfa_avg"]), 4),
            pfa_max=round(float(row["pfa_max"]), 4),
            overall_avg=round(float(row["overall_avg"]), 4)
        )
        for _, row in grouped.iterrows()
    ]

    return NationsResponse(nations=result)


@router.get("/nations/africa", response_model=NationsResponse)
def compare_african_nations():
    """Comparaison des nations africaines uniquement."""
    df_players = get_players()
    african_nations = [
        "Morocco", "Algeria", "Tunisia", "Egypt", "Senegal", "Nigeria",
        "Ivory Coast", "Cameroon", "Ghana", "Mali", "Burkina Faso",
        "South Africa", "DR Congo", "Guinea", "Tanzania"
    ]
    result = []

    if "nationality_name" in df_players.columns:
        for nation in african_nations:
            mask = df_players["nationality_name"] == nation
            if mask.sum() > 0:
                sub = df_players[mask]
                result.append(NationStats(
                    nation=nation,
                    players_count=int(mask.sum()),
                    pfa_avg=round(float(sub["pfa_score"].mean()), 4),
                    pfa_max=round(float(sub["pfa_score"].max()), 4),
                    overall_avg=round(float(sub["overall_raw"].mean()), 4)
                ))

    return NationsResponse(nations=result)
