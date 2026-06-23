"""
=============================================================
data_loader.py — Chargement unique des données et modèles
=============================================================
"""

import os
import json
import torch
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from model import GNN

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Variables globales
data           = None
model          = None
model_holdout  = None
df_players     = None
pfa_vector     = None
ALL_FEATURES   = []
EXCLUSIONS     = ["y. belhanda", "f. fajr", "k. boutaib", "m. boussoufa"]


def load_all_data():
    """Charge toutes les données et modèles au démarrage."""
    global data, model, model_holdout, df_players, pfa_vector, ALL_FEATURES

    print("  [1/6] Chargement du graphe...")
    data = torch.load(os.path.join(BASE_DIR, "graph_data.pt"), weights_only=False)
    print(f"        Graphe : {data.x.shape[0]:,} nœuds, {data.edge_index.shape[1]:,} arêtes")

    print("  [2/6] Chargement du modèle GNN complet...")
    IN_DIM, HIDDEN, OUT_DIM = data.x.shape[1], 128, 64
    model = GNN(IN_DIM, HIDDEN, OUT_DIM)
    model.load_state_dict(torch.load(
        os.path.join(BASE_DIR, "gnn_model.pt"), weights_only=True
    ))
    model.eval()
    print(f"        Modèle chargé : {sum(p.numel() for p in model.parameters()):,} paramètres")

    print("  [3/6] Chargement du modèle holdout...")
    model_holdout = GNN(IN_DIM, HIDDEN, OUT_DIM)
    model_holdout.load_state_dict(torch.load(
        os.path.join(BASE_DIR, "gnn_model_holdout.pt"), weights_only=True
    ))
    model_holdout.eval()
    print(f"        Modèle holdout chargé")

    print("  [4/6] Chargement des joueurs...")
    df_players = pd.read_csv(os.path.join(BASE_DIR, "players_final.csv"), encoding="utf-8")
    print(f"        Joueurs : {len(df_players):,}")

    print("  [5/6] Chargement du vecteur PFA...")
    with open(os.path.join(BASE_DIR, "pfa_vector.json"), encoding="utf-8") as f:
        pfa_vector = json.load(f)
    ALL_FEATURES.clear()
    ALL_FEATURES.extend([f for f in pfa_vector.keys() if f in df_players.columns])
    print(f"        Vecteur PFA : {len(pfa_vector)} dimensions")

    print("  [6/6] Calcul des scores PFA...")
    _compute_pfa_scores()
    print(f"        Scores PFA calculés (champ + gardien)")

    # Statistiques par nation
    if "nationality_name" in df_players.columns:
        n_nations = df_players["nationality_name"].nunique()
    else:
        n_nations = 0

    print("=" * 55)
    print("  BACKEND PRÊT ✅")
    print(f"  Joueurs : {len(df_players):,}")
    print(f"  Nations : {n_nations}")
    print(f"  Marocains : {(df_players['is_moroccan'] == 1).sum()}")
    print("=" * 55)


def _compute_pfa_scores():
    """Calcule les scores PFA pour tous les joueurs (GNN + overall blend)."""
    global df_players

    # 1. Scores GNN pour tous les joueurs
    with torch.no_grad():
        _, scores_gnn = model(data.x, data.edge_index)
    gnn_scores = scores_gnn.numpy().astype(np.float64)

    # 2. Score overall normalisé (colonne already [0,1])
    overall_norm = df_players["overall"].fillna(0.5).values

    # 3. Joueurs de champ : 70% GNN + 30% overall
    # L'imputation StatsBomb a homogénéisé les features par poste, ce qui comprime
    # les scores GNN. Le blend avec overall rétablit la hiérarchie qualitative.
    mask_gkp = (df_players["poste"] == "GKP").values
    mask_out = ~mask_gkp
    df_players["pfa_score"] = np.where(
        mask_out,
        0.70 * gnn_scores + 0.30 * overall_norm,
        gnn_scores  # placeholder remplacé ci-dessous pour GKP
    )

    # 4. Gardiens : cosine_similarity(features, pfa_gkp) × 65% + overall × 35%
    pfa_gkp = {
        "pace": 0.55, "shooting": 0.20, "passing": 0.65,
        "dribbling": 0.40, "defending": 0.60, "physic": 0.75,
        "power_stamina": 0.70, "mentality_interceptions": 0.60,
        "goalkeeping_diving": 0.85, "goalkeeping_handling": 0.82,
        "goalkeeping_kicking": 0.78, "goalkeeping_positioning": 0.83,
        "goalkeeping_reflexes": 0.87,
        "pass_accuracy": 0.70, "duel_win_rate": 0.55,
        "pressings": 0.50, "carries": 0.40, "goal_ratio": 0.10,
    }
    pfa_gkp_vec = np.array([pfa_gkp.get(f, 0.5) for f in ALL_FEATURES])

    if mask_gkp.sum() > 0:
        X_gkp = df_players.loc[mask_gkp, ALL_FEATURES].fillna(0.0).values
        scores_gkp = cosine_similarity(X_gkp, pfa_gkp_vec.reshape(1, -1)).flatten()
        gkp_overall = df_players.loc[mask_gkp, "overall"].fillna(0.5).values
        df_players.loc[mask_gkp, "pfa_score"] = 0.65 * scores_gkp + 0.35 * gkp_overall


# ─────────────────────────────────────────────
# ACCESSEURS
# ─────────────────────────────────────────────
def get_data():           return data
def get_model():          return model
def get_model_holdout():  return model_holdout
def get_players():        return df_players
def get_pfa_vector():     return pfa_vector
def get_features():       return ALL_FEATURES
def get_exclusions():     return EXCLUSIONS
