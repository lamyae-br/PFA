"""
=============================================================
schemas.py — Schémas Pydantic pour les réponses API
=============================================================
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict


# ─────────────────────────────────────────────
# JOUEUR
# ─────────────────────────────────────────────
class Player(BaseModel):
    """Représente un joueur de football."""
    model_config = ConfigDict(protected_namespaces=())

    short_name:  str
    poste:       str
    club:        str
    overall:     int
    pfa_score:   float
    nationality: str


class PlayerDetail(Player):
    """Joueur avec features détaillées."""
    is_moroccan: bool
    features: Dict[str, float]


# ─────────────────────────────────────────────
# COMPOSITION
# ─────────────────────────────────────────────
class CompositionResponse(BaseModel):
    """Composition d'équipe optimale."""
    model_config = ConfigDict(protected_namespaces=())

    formation:    str
    nation:       Optional[str] = None
    players:      List[Player]
    total_pfa:    float


# ─────────────────────────────────────────────
# VECTEUR PFA
# ─────────────────────────────────────────────
class PFAVectorResponse(BaseModel):
    dimensions:  int
    vector:      Dict[str, float]
    description: str


# ─────────────────────────────────────────────
# STATISTIQUES
# ─────────────────────────────────────────────
class Stats(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    total_players:    int
    moroccan_players: int
    total_nations:    int
    total_edges:      int
    features:         int
    gnn_r2:           float
    gnn_mae:          float
    holdout_r2:       float


# ─────────────────────────────────────────────
# NATIONS
# ─────────────────────────────────────────────
class NationStats(BaseModel):
    nation:        str
    players_count: int
    pfa_avg:       float
    pfa_max:       float
    overall_avg:   float


class NationsResponse(BaseModel):
    nations: List[NationStats]


class NationListItem(BaseModel):
    nation:        str
    players_count: int


class NationsListResponse(BaseModel):
    total:   int
    nations: List[NationListItem]


# ─────────────────────────────────────────────
# TOP JOUEURS PAR POSTE
# ─────────────────────────────────────────────
class TopPlayer(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    name:        str
    club:        str
    nationality: str
    overall:     int
    pfa_score:   float


class TopPlayersResponse(BaseModel):
    nation: Optional[str] = None
    GKP:    List[TopPlayer]
    DEF:    List[TopPlayer]
    MIL:    List[TopPlayer]
    ATT:    List[TopPlayer]
