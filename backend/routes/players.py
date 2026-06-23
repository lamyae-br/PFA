"""
routes/players.py — Endpoints joueurs MULTI-NATIONS
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from schemas import Player, PlayerDetail
from data_loader import get_players, get_features
from dependencies import get_current_user

router = APIRouter()


@router.get("/players", response_model=List[Player])
def get_players_endpoint(
    nation: Optional[str] = Query(None, description="Nationalité (vide = mondial)"),
    poste:  Optional[str] = Query(None, description="Poste : GKP, DEF, MIL, ATT"),
    min_pfa: float = Query(0.0, description="Score PFA minimum"),
    limit:  int   = Query(50,  description="Nombre max"),
    _user: dict = Depends(get_current_user),
):
    """
    Liste des joueurs avec filtres optionnels (nation, poste, score min).
    """
    df_players = get_players()
    df = df_players.copy()

    if nation and "nationality_name" in df.columns:
        df = df[df["nationality_name"] == nation]
    if poste:
        df = df[df["poste"] == poste.upper()]
    if min_pfa > 0:
        df = df[df["pfa_score"] >= min_pfa]

    df = df.nlargest(limit, "pfa_score")

    return [
        Player(
            short_name=str(row.get("short_name", "?")),
            poste=str(row.get("poste", "?")),
            club=str(row.get("club_name", "?")),
            overall=int(row.get("overall_raw", 0)),
            pfa_score=round(float(row.get("pfa_score", 0)), 4),
            nationality=str(row.get("nationality_name", "?"))
        )
        for _, row in df.iterrows()
    ]


@router.get("/players/morocco", response_model=List[Player])
def get_moroccan_players(
    poste: Optional[str] = Query(None, description="Filtrer par poste"),
    limit: int = Query(50),
    _user: dict = Depends(get_current_user),
):
    """Liste des joueurs marocains (raccourci historique)."""
    df_players = get_players()
    df_maroc = df_players[df_players["is_moroccan"] == 1].copy()

    if poste:
        df_maroc = df_maroc[df_maroc["poste"] == poste.upper()]

    df_maroc = df_maroc.nlargest(limit, "pfa_score")

    return [
        Player(
            short_name=str(row.get("short_name", "?")),
            poste=str(row.get("poste", "?")),
            club=str(row.get("club_name", "?")),
            overall=int(row.get("overall_raw", 0)),
            pfa_score=round(float(row.get("pfa_score", 0)), 4),
            nationality="Morocco"
        )
        for _, row in df_maroc.iterrows()
    ]


@router.get("/players/search")
def search_players(
    q:     str = Query("",  description="Recherche par nom (min 2 caractères)"),
    limit: int = Query(10,  description="Nombre max de résultats", le=30),
    _user: dict = Depends(get_current_user),
):
    """Autocomplete : retourne les joueurs dont le nom contient q."""
    df_players = get_players()
    if len(q.strip()) < 2:
        return []
    matches = df_players[
        df_players["short_name"].str.lower().str.contains(q.strip().lower(), na=False)
    ].head(limit)
    return [
        {
            "short_name":  str(r["short_name"]),
            "poste":       str(r["poste"]),
            "club":        str(r["club_name"]),
            "nationality": str(r["nationality_name"]),
            "overall":     int(r["overall_raw"]),
            "pfa_score":   round(float(r["pfa_score"]), 4),
        }
        for _, r in matches.iterrows()
    ]


@router.get("/players/{name}", response_model=PlayerDetail)
def get_player_by_name(name: str, _user: dict = Depends(get_current_user)):
    """Détails complets d'un joueur (recherche partielle par nom)."""
    df_players = get_players()
    ALL_FEATURES = get_features()

    matches = df_players[
        df_players["short_name"].str.lower().str.contains(name.lower(), na=False)
    ]

    if len(matches) == 0:
        raise HTTPException(status_code=404, detail=f"Joueur '{name}' introuvable")

    row = matches.iloc[0]
    return PlayerDetail(
        short_name=str(row.get("short_name", "?")),
        poste=str(row.get("poste", "?")),
        club=str(row.get("club_name", "?")),
        overall=int(row.get("overall_raw", 0)),
        pfa_score=round(float(row.get("pfa_score", 0)), 4),
        nationality=str(row.get("nationality_name", "?")),
        is_moroccan=bool(row.get("is_moroccan", 0) == 1),
        features={
            f: round(float(row.get(f, 0)), 4)
            for f in ALL_FEATURES if f in row.index
        }
    )
