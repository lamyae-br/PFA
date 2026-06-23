"""
routes/editor.py — Éditeur PFA interactif
Recalcul instantané de la composition avec un vecteur PFA custom (cosinus 18D).
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List, Dict
from pydantic import BaseModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from data_loader import get_players, get_pfa_vector, get_features, get_exclusions
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


# ─────────────────────────────────────────────
# Schémas
# ─────────────────────────────────────────────

class EditorRequest(BaseModel):
    vector:    Dict[str, float]
    formation: str = "4-3-3"
    nation:    Optional[str] = None


class EditorPlayer(BaseModel):
    short_name:   str
    poste:        str
    club:         str
    nationality:  str
    overall:      int
    custom_score: float   # cosinus avec le vecteur custom
    gnn_score:    float   # score GNN original
    is_new:       bool    # True si absent de la composition GNN


class EditorResponse(BaseModel):
    formation:      str
    nation:         str
    players:        List[EditorPlayer]
    total_score:    float    # somme des custom_scores des 11
    original_total: float    # somme des gnn_scores de la composition GNN
    entrants:       List[str]
    sortants:       List[str]


# ─────────────────────────────────────────────
# Vecteur par défaut
# ─────────────────────────────────────────────

@router.get("/editor/default-vector")
def get_default_vector(_user: dict = Depends(get_current_user)):
    """Retourne le vecteur PFA d'origine (depuis pfa_vector.json)."""
    return get_pfa_vector()


# ─────────────────────────────────────────────
# Composition avec vecteur custom
# ─────────────────────────────────────────────

@router.post("/editor/composition", response_model=EditorResponse)
def editor_composition(
    req:   EditorRequest,
    _user: dict = Depends(get_current_user),
):
    """
    Recalcule la composition optimale à partir d'un vecteur PFA custom.
    Score = cosinus(features_joueur_18D, pfa_custom_18D).
    Le delta (entrants/sortants) compare avec la composition GNN par défaut.
    """
    df_all   = get_players()
    features = get_features()   # liste ordonnée de 18 features
    EXCLUSIONS = get_exclusions()

    if req.formation not in FORMATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formation '{req.formation}' non supportée. Choisir parmi : {list(FORMATIONS.keys())}"
        )

    # ── Filtrer par nation ──
    if req.nation:
        if "nationality_name" not in df_all.columns:
            raise HTTPException(status_code=400, detail="Colonne nationality_name manquante")
        df = df_all[df_all["nationality_name"] == req.nation].copy()
        if len(df) == 0:
            raise HTTPException(status_code=404, detail=f"Nation '{req.nation}' introuvable")
        if req.nation == "Morocco":
            df = df[~df["short_name"].str.lower().isin(EXCLUSIONS)]
    else:
        df = df_all.copy()

    # ── Construire le vecteur PFA custom (clamp 0–1) ──
    pfa_custom = np.array(
        [float(req.vector.get(f, 0.5)) for f in features],
        dtype=np.float32
    )
    pfa_custom = np.clip(pfa_custom, 0.0, 1.0)

    # ── Calcul cosinus pour tous les joueurs (vectorisé, < 5ms) ──
    X = df[features].fillna(0.0).values.astype(np.float32)    # (N, 18)
    custom_scores = cosine_similarity(X, pfa_custom.reshape(1, -1)).flatten()
    df = df.copy()
    df["custom_score"] = custom_scores

    # ── Composition GNN de référence (pour le delta) ──
    FORMATION = FORMATIONS[req.formation]
    original_names: set = set()
    for poste, nb in FORMATION.items():
        top = df[df["poste"] == poste].nlargest(nb, "pfa_score")
        original_names.update(top["short_name"].tolist())

    rows_orig   = df[df["short_name"].isin(original_names)]
    original_total = float(rows_orig["pfa_score"].sum())

    # ── Nouvelle composition (basée sur custom_score) ──
    custom_players: List[EditorPlayer] = []
    for poste, nb in FORMATION.items():
        top = df[df["poste"] == poste].nlargest(nb, "custom_score")
        if len(top) < nb:
            raise HTTPException(
                status_code=400,
                detail=f"Pas assez de joueurs au poste {poste} pour '{req.nation or 'mondial'}'. "
                       f"Trouvé {len(top)}/{nb}."
            )
        for _, row in top.iterrows():
            name = str(row["short_name"])
            custom_players.append(EditorPlayer(
                short_name   = name,
                poste        = poste,
                club         = str(row.get("club_name", "?")),
                nationality  = str(row.get("nationality_name", req.nation or "World")),
                overall      = int(row.get("overall_raw", 0)),
                custom_score = round(float(row["custom_score"]), 4),
                gnn_score    = round(float(row.get("pfa_score", 0)), 4),
                is_new       = name not in original_names,
            ))

    custom_names = {p.short_name for p in custom_players}
    entrants     = [p.short_name for p in custom_players if p.is_new]
    sortants     = [n for n in original_names if n not in custom_names]
    total_score  = round(sum(p.custom_score for p in custom_players), 4)

    return EditorResponse(
        formation      = req.formation,
        nation         = req.nation or "World",
        players        = custom_players,
        total_score    = total_score,
        original_total = round(original_total, 4),
        entrants       = entrants,
        sortants       = sortants,
    )
