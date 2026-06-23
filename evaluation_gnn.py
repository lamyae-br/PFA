"""
=============================================================
evaluation_gnn.py — Évaluation complète du modèle GNN
=============================================================
Entrée  : graph_data.pt, gnn_model.pt, players_final.csv,
          split_masks.pt, pfa_vector.json
Sortie  : evaluation_results.csv
          evaluation_report.txt
=============================================================
Méthode : Comparaison GNN vs baselines ML sur la prédiction
          de la similarité PFA (ground truth réel).
          Le GNN est meilleur s'il exploite la structure du
          graphe (contexte réseau) mieux que les features seules.
=============================================================
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
import pandas as pd
import numpy as np
import json, warnings
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
warnings.filterwarnings("ignore")

print("=" * 58)
print("  ÉVALUATION COMPLÈTE DU MODÈLE GNN")
print("=" * 58)

# ---------------------------------------------
# ARCHITECTURE (identique à l'entraînement)
# ---------------------------------------------
class GNN(nn.Module):
    def __init__(self, in_dim, hidden, out_dim):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden)
        self.bn1   = nn.BatchNorm1d(hidden)
        self.conv2 = SAGEConv(hidden, hidden)
        self.bn2   = nn.BatchNorm1d(hidden)
        self.conv3 = SAGEConv(hidden, out_dim)
        self.bn3   = nn.BatchNorm1d(out_dim)
        self.head  = nn.Sequential(
            nn.Linear(out_dim, 32), nn.ReLU(),
            nn.Dropout(0.2), nn.Linear(32, 1), nn.Sigmoid(),
        )

    def encode(self, x, edge_index):
        x = self.bn1(F.relu(self.conv1(x, edge_index)))
        x = F.dropout(x, p=0.0, training=False)
        x = self.bn2(F.relu(self.conv2(x, edge_index)))
        x = F.dropout(x, p=0.0, training=False)
        return self.bn3(self.conv3(x, edge_index))

    def forward(self, x, edge_index):
        emb = self.encode(x, edge_index)
        return emb, self.head(emb).squeeze(-1)

# ---------------------------------------------
# ETAPE 1 — CHARGEMENT
# ---------------------------------------------
print("\n[1] Chargement des données...")

data       = torch.load("graph_data.pt",   weights_only=False)
df_players = pd.read_csv("players_final.csv", encoding="utf-8")
pfa_dict   = json.load(open("pfa_vector.json", encoding="utf-8"))

IN_DIM, HIDDEN, OUT_DIM = data.x.shape[1], 128, 64

model = GNN(IN_DIM, HIDDEN, OUT_DIM)
model.load_state_dict(torch.load("gnn_model.pt", weights_only=True))
model.eval()

print(f"    Nœuds    : {data.x.shape[0]:,}")
print(f"    Arêtes   : {data.edge_index.shape[1]:,}")
print(f"    Features : {data.x.shape[1]}")

# ✅ CORRECTION — Ground truth = similarité PFA (data.y)
# On n'utilise PLUS data.overall (FIFA)
# car le GNN est entraîné sur la similarité PFA
y_true = data.y.numpy()
print(f"    Ground truth : similarité PFA [OK]")
print(f"    y range      : min={y_true.min():.3f} max={y_true.max():.3f}")

# Split masks (train/val)
try:
    masks = torch.load("split_masks.pt", weights_only=True)
    train_mask = masks["train_mask"].numpy()
    val_mask   = masks["val_mask"].numpy()
    print(f"    Masques chargés : train={train_mask.sum():,} / val={val_mask.sum():,}")
except FileNotFoundError:
    n = data.x.shape[0]
    np.random.seed(42)
    perm = np.random.permutation(n)
    split = int(0.8 * n)
    train_mask = np.zeros(n, dtype=bool)
    val_mask   = np.zeros(n, dtype=bool)
    train_mask[perm[:split]] = True
    val_mask[perm[split:]]   = True
    print(f"    Masques générés : train={train_mask.sum():,} / val={val_mask.sum():,}")

# ---------------------------------------------
# ETAPE 2 — PRÉDICTIONS GNN
# ---------------------------------------------
print("\n[2] Prédictions GNN...")

with torch.no_grad():
    embeddings, scores_gnn = model(data.x, data.edge_index)

y_pred_gnn = scores_gnn.numpy()
df_players["pfa_score_gnn"] = y_pred_gnn

print(f"    Scores GNN : min={y_pred_gnn.min():.4f} | max={y_pred_gnn.max():.4f} | moy={y_pred_gnn.mean():.4f}")

# ---------------------------------------------
# ETAPE 3 — FEATURES POUR BASELINES
# ---------------------------------------------
print("\n[3] Préparation features baselines...")

ALL_FEATURES = list(pfa_dict.keys())
ALL_FEATURES = [c for c in ALL_FEATURES if c in df_players.columns]

X_all    = df_players[ALL_FEATURES].fillna(0).values
y_all    = y_true  # ✅ similarité PFA pour tout le monde

X_train  = X_all[train_mask]
X_test   = X_all[val_mask]
y_train  = y_all[train_mask]
y_test   = y_all[val_mask]

y_gnn_test = y_pred_gnn[val_mask]

print(f"    Features : {len(ALL_FEATURES)}")
print(f"    Train    : {len(X_train):,}")
print(f"    Test     : {len(X_test):,}")

# ---------------------------------------------
# ETAPE 4 — BASELINES ML
# ---------------------------------------------
print("\n[4] Entraînement des baselines ML...")

baselines = {
    "Ridge"            : Ridge(alpha=1.0),
    "KNN (k=5)"        : KNeighborsRegressor(n_neighbors=5),
    "Decision Tree"    : DecisionTreeRegressor(max_depth=6, random_state=42),
    "Gradient Boosting": GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42),
}

results = {}

# Ajouter GNN directement
mae_gnn  = mean_absolute_error(y_test, y_gnn_test)
rmse_gnn = np.sqrt(mean_squared_error(y_test, y_gnn_test))
r2_gnn   = r2_score(y_test, y_gnn_test)
results["GNN (notre modèle)"] = {"MAE": mae_gnn, "RMSE": rmse_gnn, "R2": r2_gnn}

# Moyenne naïve
y_pred_mean = np.full_like(y_test, y_train.mean())
results["Moyenne naïve"] = {
    "MAE" : mean_absolute_error(y_test, y_pred_mean),
    "RMSE": np.sqrt(mean_squared_error(y_test, y_pred_mean)),
    "R2"  : r2_score(y_test, y_pred_mean),
}

# Baselines ML
for name, clf in baselines.items():
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    results[name] = {
        "MAE" : mean_absolute_error(y_test, y_pred),
        "RMSE": np.sqrt(mean_squared_error(y_test, y_pred)),
        "R2"  : r2_score(y_test, y_pred),
    }
    print(f"    {name:<20} -> MAE={results[name]['MAE']:.4f}  R²={results[name]['R2']:.4f}")

# ---------------------------------------------
# ETAPE 5 — TEST OVERFITTING
# ---------------------------------------------
print("\n[5] Test Train/Test split GNN...")

y_gnn_train  = y_pred_gnn[train_mask]
mae_train    = mean_absolute_error(y_train, y_gnn_train)
mae_test_gnn = results["GNN (notre modèle)"]["MAE"]
overfitting  = "OUI [!]" if mae_test_gnn > mae_train * 1.5 else "NON [OK]"

print(f"    MAE Train : {mae_train:.6f}")
print(f"    MAE Test  : {mae_test_gnn:.6f}")
print(f"    Overfitting : {overfitting}")

# ---------------------------------------------
# ETAPE 6 — TEST MAROC vs MONDE
# ---------------------------------------------
print("\n[6] Analyse Maroc vs Reste du monde...")

if "is_moroccan" in df_players.columns:
    maroc_mask     = df_players["is_moroccan"].values == 1
    non_maroc_mask = ~maroc_mask

    mae_maroc     = mean_absolute_error(y_true[maroc_mask], y_pred_gnn[maroc_mask])
    mae_non_maroc = mean_absolute_error(y_true[non_maroc_mask], y_pred_gnn[non_maroc_mask])

    print(f"    Joueurs marocains    : {maroc_mask.sum()}")
    print(f"    MAE sur Marocains    : {mae_maroc:.6f}")
    print(f"    MAE sur non-Marocains: {mae_non_maroc:.6f}")

    if mae_maroc < mae_non_maroc * 1.2:
        print(f"    -> Modèle performant sur les Marocains [OK]")
    else:
        print(f"    -> Modèle moins précis sur les Marocains (holdout non utilisé)")
else:
    print("    Colonne is_moroccan non trouvée")
    maroc_mask = np.zeros(len(df_players), dtype=bool)

# ---------------------------------------------
# ETAPE 7 — TABLEAU COMPARATIF
# ---------------------------------------------
print(f"\n[7] Tableau de comparaison...")

# ✅ Titre corrigé — ground truth = similarité PFA
print(f"\n{'='*62}")
print(f"  COMPARAISON DES MÉTHODES (Ground truth = similarité PFA)")
print(f"{'='*62}")
print(f"  {'Méthode':<25} {'MAE':>8} {'RMSE':>8} {'R²':>8} {'vs Ridge':>10}")
print(f"  {'-'*60}")

mae_ridge = results.get("Ridge", {"MAE": 1.0})["MAE"]
for methode, res in results.items():
    amelio = ((mae_ridge - res["MAE"]) / (mae_ridge + 1e-8) * 100)
    flag = " <- GNN" if methode == "GNN (notre modèle)" else ""
    print(f"  {methode:<25} {res['MAE']:>8.4f} {res['RMSE']:>8.4f} {res['R2']:>8.4f} {amelio:>+9.1f}%{flag}")

print(f"{'='*62}")

# ---------------------------------------------
# ETAPE 8 — NATIONS SIMILAIRES AU MAROC
# ---------------------------------------------
print(f"\n[8] Comparaison avec nations similaires...")

if "nationality_name" in df_players.columns:
    nations = ["Morocco", "Algeria", "Tunisia", "Egypt", "Senegal", "Nigeria", "Ivory Coast"]
    nations = [n for n in nations if n in df_players["nationality_name"].values]

    print(f"\n  {'Nation':<18} {'Joueurs':>8} {'GNN moy':>10} {'GNN max':>10} {'PFA moy':>12}")
    print(f"  {'-'*60}")

    for nation in nations:
        mask = df_players["nationality_name"].values == nation
        sc   = y_pred_gnn[mask]
        pfa  = y_true[mask]  # ✅ PFA réel au lieu de overall FIFA
        flag = " <- cible" if nation == "Morocco" else ""
        print(f"  {nation:<18} {mask.sum():>8} {sc.mean():>10.4f} {sc.max():>10.4f} {pfa.mean():>12.4f}{flag}")

# ---------------------------------------------
# ETAPE 9 — TOP JOUEURS MAROCAINS
# ---------------------------------------------
print(f"\n[9] Top joueurs marocains par GNN score...")

if maroc_mask.sum() > 0:
    df_maroc_eval = df_players[maroc_mask].copy()
    df_maroc_eval["pfa_score_gnn"] = y_pred_gnn[maroc_mask]

    for poste in ["GKP", "DEF", "MIL", "ATT"]:
        if "poste" in df_maroc_eval.columns:
            sub = df_maroc_eval[df_maroc_eval["poste"] == poste].nlargest(3, "pfa_score_gnn")
        else:
            sub = pd.DataFrame()
        if len(sub) > 0:
            noms = " | ".join(sub["short_name"].tolist())
            print(f"    {poste} : {noms}")

# ---------------------------------------------
# ETAPE 10 — SAUVEGARDE
# ---------------------------------------------
print(f"\n[10] Sauvegarde des résultats...")

df_results = pd.DataFrame([
    {"Méthode": m, "MAE": r["MAE"], "RMSE": r["RMSE"], "R2": r["R2"]}
    for m, r in results.items()
])
df_results.to_csv("evaluation_results.csv", index=False, encoding="utf-8")

with open("evaluation_report.txt", "w", encoding="utf-8") as f:
    f.write("RAPPORT D'ÉVALUATION — GNN SÉLECTION NATIONALE MAROC\n")
    f.write("=" * 58 + "\n\n")
    f.write(f"Dataset\n")
    f.write(f"  Joueurs total     : {len(df_players):,}\n")
    f.write(f"  Joueurs marocains : {maroc_mask.sum()}\n")
    f.write(f"  Arêtes            : {data.edge_index.shape[1]:,}\n")
    f.write(f"  Features          : {IN_DIM}\n\n")
    f.write(f"Overfitting\n")
    f.write(f"  MAE Train         : {mae_train:.6f}\n")
    f.write(f"  MAE Test          : {mae_test_gnn:.6f}\n")
    f.write(f"  Overfitting       : {overfitting}\n\n")
    if maroc_mask.sum() > 0:
        f.write(f"Performance Maroc vs Monde\n")
        f.write(f"  MAE Marocains     : {mae_maroc:.6f}\n")
        f.write(f"  MAE Non-Marocains : {mae_non_maroc:.6f}\n\n")
    f.write(f"Comparaison des méthodes (Ground truth = similarité PFA)\n")
    f.write(f"  {'Méthode':<25} {'MAE':>8} {'RMSE':>8} {'R2':>8}\n")
    f.write(f"  {'-'*50}\n")
    for m, r in results.items():
        f.write(f"  {m:<25} {r['MAE']:>8.4f} {r['RMSE']:>8.4f} {r['R2']:>8.4f}\n")

print(f"    evaluation_results.csv -> sauvegardé [OK]")
print(f"    evaluation_report.txt  -> sauvegardé [OK]")

print(f"\n{'='*58}")
print(f"  ÉVALUATION TERMINÉE")
print(f"{'='*58}")
print(f"  evaluation_results.csv -> tableau de comparaison")
print(f"  evaluation_report.txt  -> rapport complet")
print(f"{'='*58}")