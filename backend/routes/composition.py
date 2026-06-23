"""
routes/composition.py — Composition optimale MULTI-NATIONS
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional
from schemas import CompositionResponse, Player, TopPlayersResponse, TopPlayer
from data_loader import get_players, get_exclusions
from dependencies import get_current_user

router = APIRouter()

FORMATIONS = {
    "4-3-3":   {"GKP": 1, "DEF": 4, "MIL": 3, "ATT": 3},
    "4-4-2":   {"GKP": 1, "DEF": 4, "MIL": 4, "ATT": 2},
    "4-2-3-1": {"GKP": 1, "DEF": 4, "MIL": 5, "ATT": 1},
    "3-5-2":   {"GKP": 1, "DEF": 3, "MIL": 5, "ATT": 2},
    "3-4-3":   {"GKP": 1, "DEF": 3, "MIL": 4, "ATT": 3},
    "5-3-2":   {"GKP": 1, "DEF": 5, "MIL": 3, "ATT": 2},
}


@router.get("/composition", response_model=CompositionResponse)
def get_composition(
    formation: str = Query("4-3-3", description=f"Formation : {list(FORMATIONS.keys())}"),
    nation: Optional[str] = Query(None, description="Nationalité (ex: Morocco, France, Brazil). Vide = mondial."),
    _user: dict = Depends(get_current_user),
):
    """
    Composition optimale selon la formation et la nationalité.

    Exemples :
    - `/api/composition` → meilleur XI mondial
    - `/api/composition?nation=Morocco` → meilleur XI marocain
    - `/api/composition?nation=France` → meilleur XI français
    - `/api/composition?nation=Brazil&formation=4-2-3-1` → Brésil en 4-2-3-1
    """
    df_players = get_players()
    EXCLUSIONS = get_exclusions()

    if formation not in FORMATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formation '{formation}' non supportée. Choisir parmi : {list(FORMATIONS.keys())}"
        )

    # Filtrer par nationalité
    if nation:
        if "nationality_name" not in df_players.columns:
            raise HTTPException(status_code=400, detail="Colonne nationality_name manquante")
        df_filtered = df_players[df_players["nationality_name"] == nation].copy()
        if len(df_filtered) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Aucun joueur trouvé pour '{nation}'. Vérifie : Morocco, France, Brazil, Argentina, Spain..."
            )
    else:
        df_filtered = df_players.copy()

    # Filtre joueurs retirés (uniquement Maroc)
    if nation == "Morocco":
        df_filtered = df_filtered[~df_filtered["short_name"].str.lower().isin(EXCLUSIONS)]

    # Supprimer les doublons : même joueur, même poste → garder le meilleur score
    df_filtered = (
        df_filtered
        .sort_values("pfa_score", ascending=False)
        .drop_duplicates(subset=["short_name", "nationality_name", "poste"])
    )

    FORMATION = FORMATIONS[formation]
    composition = []

    for poste, nb in FORMATION.items():
        top = df_filtered[df_filtered["poste"] == poste].nlargest(nb, "pfa_score")
        if len(top) < nb:
            raise HTTPException(
                status_code=400,
                detail=f"Pas assez de joueurs au poste {poste} pour '{nation or 'mondial'}'. "
                       f"Trouvé {len(top)}/{nb}."
            )
        for _, row in top.iterrows():
            composition.append(Player(
                short_name=str(row.get("short_name", "?")),
                poste=poste,
                club=str(row.get("club_name", "?")),
                overall=int(row.get("overall_raw", 0)),
                pfa_score=round(float(row.get("pfa_score", 0)), 4),
                nationality=str(row.get("nationality_name", nation or "World"))
            ))

    total_pfa = round(sum(p.pfa_score for p in composition), 4)

    return CompositionResponse(
        formation=formation,
        nation=nation or "World",
        players=composition,
        total_pfa=total_pfa
    )


@router.get("/top-players", response_model=TopPlayersResponse)
def get_top_players(
    nation: Optional[str] = Query(None, description="Filtrer par nation (vide = mondial)"),
    _user: dict = Depends(get_current_user),
):
    """Top 3 joueurs par poste — mondial ou par nation."""
    df_players = get_players()
    EXCLUSIONS = get_exclusions()

    if nation:
        df_filtered = df_players[df_players["nationality_name"] == nation].copy()
        if len(df_filtered) == 0:
            raise HTTPException(status_code=404, detail=f"Nation '{nation}' introuvable")
        if nation == "Morocco":
            df_filtered = df_filtered[~df_filtered["short_name"].str.lower().isin(EXCLUSIONS)]
    else:
        df_filtered = df_players.copy()

    df_filtered = (
        df_filtered
        .sort_values("pfa_score", ascending=False)
        .drop_duplicates(subset=["short_name", "nationality_name", "poste"])
    )

    result = {"nation": nation or "World"}
    for poste in ["GKP", "DEF", "MIL", "ATT"]:
        top3 = df_filtered[df_filtered["poste"] == poste].nlargest(3, "pfa_score")
        result[poste] = [
            TopPlayer(
                name=str(row.get("short_name", "?")),
                club=str(row.get("club_name", "?")),
                nationality=str(row.get("nationality_name", "?")),
                overall=int(row.get("overall_raw", 0)),
                pfa_score=round(float(row.get("pfa_score", 0)), 4)
            )
            for _, row in top3.iterrows()
        ]

    return TopPlayersResponse(**result)


@router.get("/nations-list")
def get_nations_list(
    min_players: int = Query(11, description="Minimum de joueurs (au moins 11 pour pouvoir composer un XI)")
):
    """
    Liste de toutes les nationalités disponibles.
    Utile pour le dropdown du frontend.
    """
    df_players = get_players()

    if "nationality_name" not in df_players.columns:
        return {"total": 0, "nations": []}

    counts = df_players["nationality_name"].value_counts()
    nations = [
        {"nation": str(name), "players_count": int(count)}
        for name, count in counts.items()
        if count >= min_players
    ]
    return {"total": len(nations), "nations": nations}
