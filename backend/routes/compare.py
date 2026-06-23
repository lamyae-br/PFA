"""
routes/compare.py — Comparaison de deux joueurs vs vecteur PFA
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List
from pydantic import BaseModel
from data_loader import get_players, get_pfa_vector, get_features
from dependencies import get_current_user

router = APIRouter()

# Features affichées dans le radar (hors gardien)
RADAR_FEATURES = [
    "pace", "shooting", "passing", "dribbling", "defending", "physic",
    "power_stamina", "mentality_interceptions",
    "pass_accuracy", "duel_win_rate", "pressings", "carries", "goal_ratio",
]

LABELS = {
    "pace":                    "Vitesse",
    "shooting":                "Tir",
    "passing":                 "Passe",
    "dribbling":               "Dribble",
    "defending":               "Défense",
    "physic":                  "Physique",
    "power_stamina":           "Endurance",
    "mentality_interceptions": "Interceptions",
    "pass_accuracy":           "Précision passe",
    "duel_win_rate":           "Duels gagnés",
    "pressings":               "Pressing",
    "carries":                 "Portée balle",
    "goal_ratio":              "Ratio buts",
}


# ─────────────────────────────────────────────
# Schémas de réponse
# ─────────────────────────────────────────────

class PlayerCompare(BaseModel):
    short_name:  str
    poste:       str
    club:        str
    nationality: str
    overall:     int
    pfa_score:   float
    features:    dict        # {feature_key: value}
    strengths:   List[str]   # top 3 labels où joueur > PFA
    weaknesses:  List[str]   # top 3 labels où joueur < PFA


class RadarPoint(BaseModel):
    feature:  str    # clé technique
    label:    str    # label lisible
    player_a: float
    player_b: float
    pfa:      float


class CompareResponse(BaseModel):
    player_a:    PlayerCompare
    player_b:    PlayerCompare
    radar:       List[RadarPoint]
    winner:      str   # "player_a" | "player_b" | "tie"
    winner_name: str


# ─────────────────────────────────────────────
# Utilitaires
# ─────────────────────────────────────────────

def _find(df, name: str):
    """Recherche exacte puis partielle insensible à la casse."""
    exact = df[df["short_name"].str.lower() == name.lower()]
    if len(exact) > 0:
        return exact.iloc[0]
    partial = df[df["short_name"].str.lower().str.contains(name.lower(), na=False)]
    if len(partial) == 0:
        raise HTTPException(status_code=404, detail=f"Joueur '{name}' introuvable.")
    return partial.iloc[0]


def _build(row, pfa_vec: dict, available: list) -> PlayerCompare:
    feats = {
        f: round(float(row.get(f) or 0), 4)
        for f in available
    }
    deltas  = {f: feats.get(f, 0) - float(pfa_vec.get(f, 0)) for f in feats}
    ranked  = sorted(deltas, key=lambda f: deltas[f], reverse=True)
    strengths  = [LABELS.get(f, f) for f in ranked[:3]  if deltas[f] >= 0]
    weaknesses = [LABELS.get(f, f) for f in ranked[-3:] if deltas[f] <  0]

    return PlayerCompare(
        short_name  = str(row.get("short_name", "?")),
        poste       = str(row.get("poste",      "?")),
        club        = str(row.get("club_name",  "?")),
        nationality = str(row.get("nationality_name", "?")),
        overall     = int(row.get("overall_raw", 0)),
        pfa_score   = round(float(row.get("pfa_score", 0)), 4),
        features    = feats,
        strengths   = strengths  or ["—"],
        weaknesses  = weaknesses or ["—"],
    )


# ─────────────────────────────────────────────
# Endpoint principal
# ─────────────────────────────────────────────

@router.get("/compare", response_model=CompareResponse)
def compare_players(
    player_a: str = Query(..., description="Nom du joueur A"),
    player_b: str = Query(..., description="Nom du joueur B"),
    _user: dict   = Depends(get_current_user),
):
    """Compare deux joueurs et détermine lequel correspond le mieux au vecteur PFA."""
    df      = get_players()
    pfa_vec = get_pfa_vector()
    feats   = get_features()

    row_a = _find(df, player_a)
    row_b = _find(df, player_b)

    if row_a["short_name"].lower() == row_b["short_name"].lower():
        raise HTTPException(
            status_code=400,
            detail="Les deux joueurs sont identiques. Choisissez deux joueurs différents."
        )

    available = [f for f in feats if f in RADAR_FEATURES]

    data_a = _build(row_a, pfa_vec, available)
    data_b = _build(row_b, pfa_vec, available)

    radar = [
        RadarPoint(
            feature  = f,
            label    = LABELS.get(f, f),
            player_a = data_a.features.get(f, 0),
            player_b = data_b.features.get(f, 0),
            pfa      = round(float(pfa_vec.get(f, 0)), 4),
        )
        for f in available
    ]

    if data_a.pfa_score > data_b.pfa_score:
        winner, winner_name = "player_a", data_a.short_name
    elif data_b.pfa_score > data_a.pfa_score:
        winner, winner_name = "player_b", data_b.short_name
    else:
        winner, winner_name = "tie", "Égalité"

    return CompareResponse(
        player_a=data_a, player_b=data_b,
        radar=radar, winner=winner, winner_name=winner_name,
    )
