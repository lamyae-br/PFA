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
    Joueurs de champ : score = 0.70*cosinus(features, vecteur_custom)
    + 0.30*overall (réactif au vecteur édité). Gardiens : score PFA officiel
    conservé (logique gardien spécifique). Le delta (entrants/sortants)
    compare avec la composition GNN par défaut.
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

    # ── Vecteur PFA custom (clamp 0–1) ──
    # Construit dans le MÊME ordre que les colonnes (get_features()),
    # ce qui élimine tout décalage d'index entre le frontend et le backend.
    custom_vec = np.array([float(req.vector.get(f, 0.5)) for f in features],
                          dtype=np.float32)
    custom_vec = np.clip(custom_vec, 0.0, 1.0)

    # ── Score personnalisé : réactif au vecteur pour les joueurs de champ,
    #    stable pour les gardiens ──────────────────────────────────────────
    #
    # JOUEURS DE CHAMP :
    #   custom_score = 0.70 * cosinus(features, vecteur_custom) + 0.30 * overall
    #   Le cosinus est calculé contre le vecteur ÉDITÉ : quand l'utilisateur
    #   modifie un attribut, le classement change réellement (le cosinus est
    #   très discriminant entre profils de joueurs de champ). Au vecteur par
    #   défaut, cosinus(features, défaut) ≈ score GNN (le GNN est entraîné à
    #   reproduire cette similarité, R²=0.97) : la composition reste donc
    #   pratiquement identique à la composition normale.
    #
    # GARDIENS :
    #   On conserve le score PFA officiel (df["pfa_score"]), qui suit la
    #   logique gardien spécifique (0.65 * cosinus(features, pfa_gkp) +
    #   0.35 * overall). Les cosinus des gardiens étant tous très proches,
    #   c'est l'overall qui les départage : sans lui, le mauvais gardien
    #   serait sélectionné. Le gardien reste donc stable (Bounou).
    X = df[features].fillna(0.0).values.astype(np.float32)        # (N, 18)
    cos_custom   = cosine_similarity(X, custom_vec.reshape(1, -1)).flatten()
    overall_norm = df["overall"].fillna(0.5).values.astype(np.float32)

    field_score = 0.70 * cos_custom + 0.30 * overall_norm
    is_gkp = (df["poste"] == "GKP").values

    df = df.copy()
    df["custom_score"] = np.where(is_gkp, df["pfa_score"].values, field_score)

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
