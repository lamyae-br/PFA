"""
routes/stats.py — Statistiques globales du modèle
"""

from fastapi import APIRouter
from schemas import Stats
from data_loader import get_data, get_players

router = APIRouter()


@router.get("/stats", response_model=Stats)
def get_stats():
    """Statistiques globales du dataset et performance du modèle."""
    data       = get_data()
    df_players = get_players()

    n_nations = 0
    if "nationality_name" in df_players.columns:
        n_nations = int(df_players["nationality_name"].nunique())

    return Stats(
        total_players    = len(df_players),
        moroccan_players = int((df_players["is_moroccan"] == 1).sum()),
        total_nations    = n_nations,
        total_edges      = int(data.edge_index.shape[1]),
        features         = int(data.x.shape[1]),
        gnn_r2           = 0.9715,
        gnn_mae          = 0.0035,
        holdout_r2       = 0.8969
    )


@router.get("/evaluation")
def get_evaluation():
    """Comparaison détaillée GNN vs baselines ML."""
    return {
        "ground_truth": "similarité PFA (cosinus)",
        "methods": [
            {"name": "GNN (graphe StatsBomb)", "MAE": 0.0035, "RMSE": 0.0045, "R2": 0.9715},
            {"name": "Gradient Boosting",     "MAE": 0.0013, "RMSE": 0.0018, "R2": 0.9953},
            {"name": "KNN (k=5)",             "MAE": 0.0016, "RMSE": 0.0029, "R2": 0.9886},
            {"name": "Ridge",                 "MAE": 0.0053, "RMSE": 0.0070, "R2": 0.9317},
            {"name": "Decision Tree",         "MAE": 0.0035, "RMSE": 0.0050, "R2": 0.9647},
            {"name": "Moyenne naïve",         "MAE": 0.0192, "RMSE": 0.0268, "R2": 0.0000},
        ],
        "holdout_test": {
            "description": "Modèle entraîné SANS jamais voir les joueurs marocains",
            "moroccan_R2":  0.8969,
            "moroccan_MAE": 0.0050,
            "interpretation": "Le modèle généralise sans avoir mémorisé les Marocains."
        }
    }
