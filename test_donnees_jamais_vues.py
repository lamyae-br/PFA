"""
test_donnees_jamais_vues.py
================================================
Test de generalisation du modele GNN holdout.
Le modele holdout a ete entraine SANS les joueurs
marocains. On l'evalue ici sur :
  (1) Les joueurs marocains (jamais vus pendant entrainement)
  (2) Les joueurs de validation (20%, hors loss)
Sortie : resultats_jamais_vus.csv
================================================
"""

import os, sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.metrics.pairwise import cosine_similarity as cos_sim_sklearn
import warnings
warnings.filterwarnings("ignore")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def sp(s):
    try:
        print(s)
    except UnicodeEncodeError:
        print(str(s).encode("ascii","replace").decode("ascii"))

# ── Architecture identique a entrainement_gnn.py ────────────────────
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
            nn.Dropout(0.0), nn.Linear(32, 1), nn.Sigmoid(),
        )
    def encode(self, x, edge_index):
        x = self.bn1(F.relu(self.conv1(x, edge_index)))
        x = self.bn2(F.relu(self.conv2(x, edge_index)))
        return self.bn3(self.conv3(x, edge_index))
    def forward(self, x, edge_index):
        emb = self.encode(x, edge_index)
        return emb, self.head(emb).squeeze(-1)

# ── Chargement ──────────────────────────────────────────────────────
sp("=" * 58)
sp("  TEST SUR DONNEES JAMAIS VUES")
sp("=" * 58)
sp("\n[1] Chargement...")

data       = torch.load("graph_data.pt", weights_only=False)
df_players = pd.read_csv("players_final.csv", encoding="utf-8")
IN_DIM, HIDDEN, OUT_DIM = data.x.shape[1], 128, 64

model_holdout = GNN(IN_DIM, HIDDEN, OUT_DIM)
model_holdout.load_state_dict(torch.load("gnn_model_holdout.pt", weights_only=True))
model_holdout.eval()

model_complet = GNN(IN_DIM, HIDDEN, OUT_DIM)
model_complet.load_state_dict(torch.load("gnn_model.pt", weights_only=True))
model_complet.eval()

sp(f"    Noeuds : {data.x.shape[0]:,} | Aretes : {data.edge_index.shape[1]:,}")

# ✅ CORRECTION — Ground truth = similarité PFA (data.y)
# On n'utilise PLUS data.overall (FIFA)
y_true = data.y.numpy()
sp(f"    Ground truth : similarite PFA [OK]")
sp(f"    y range      : min={y_true.min():.3f} max={y_true.max():.3f}")

# ── Predictions ─────────────────────────────────────────────────────
sp("\n[2] Predictions des deux modeles...")

with torch.no_grad():
    _, sc_holdout = model_holdout(data.x, data.edge_index)
    _, sc_complet = model_complet(data.x,  data.edge_index)

sc_holdout = sc_holdout.numpy()
sc_complet = sc_complet.numpy()

df_players["score_holdout"] = sc_holdout
df_players["score_complet"] = sc_complet
df_players["pfa_true"]      = y_true  # ✅ renommé pfa_true

# ── Test sur joueurs marocains (jamais vus par holdout) ─────────────
sp("\n[3] Test sur joueurs MAROCAINS (exclus du holdout)...")

if "is_moroccan" in df_players.columns:
    maroc_mask = df_players["is_moroccan"].values == 1
    df_maroc   = df_players[maroc_mask].copy()

    sp(f"    Joueurs marocains : {len(df_maroc)}")

    y_true_m  = y_true[maroc_mask]
    y_ho_m    = sc_holdout[maroc_mask]
    y_comp_m  = sc_complet[maroc_mask]

    mae_ho   = mean_absolute_error(y_true_m, y_ho_m)
    mae_comp = mean_absolute_error(y_true_m, y_comp_m)
    r2_ho    = r2_score(y_true_m, y_ho_m)
    r2_comp  = r2_score(y_true_m, y_comp_m)

    sp(f"\n    {'Metrique':<20} {'Modele holdout':>16} {'Modele complet':>16}")
    sp(f"    {'-'*55}")
    sp(f"    {'MAE':<20} {mae_ho:>16.4f} {mae_comp:>16.4f}")
    sp(f"    {'R2':<20} {r2_ho:>16.4f} {r2_comp:>16.4f}")
    sp(f"    {'RMSE':<20} {np.sqrt(mean_squared_error(y_true_m,y_ho_m)):>16.4f}"
       f" {np.sqrt(mean_squared_error(y_true_m,y_comp_m)):>16.4f}")

    if mae_ho < 0.08:
        sp(f"\n    -> Excellente generalisation sur joueurs marocains [OK]")
    elif mae_ho < 0.15:
        sp(f"\n    -> Bonne generalisation (MAE={mae_ho:.4f}) [OK]")
    else:
        sp(f"\n    -> Generalisation acceptable (MAE={mae_ho:.4f})")

    # ✅ CORRECTION GARDIEN — vecteur PFA spécifique GKP
    import json
    ALL_FEATURES = ['pace', 'shooting', 'passing', 'dribbling', 'defending',
                    'physic', 'power_stamina', 'mentality_interceptions',
                    'goalkeeping_diving', 'goalkeeping_handling',
                    'goalkeeping_kicking', 'goalkeeping_positioning',
                    'goalkeeping_reflexes', 'pass_accuracy', 'duel_win_rate',
                    'pressings', 'carries', 'goal_ratio']
    ALL_FEATURES = [f for f in ALL_FEATURES if f in df_maroc.columns]

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
    pfa_gkp_vector = np.array([pfa_gkp.get(f, 0.5) for f in ALL_FEATURES])

    mask_gkp = df_maroc["poste"] == "GKP"
    if mask_gkp.sum() > 0:
        X_gkp = df_maroc.loc[mask_gkp, ALL_FEATURES].fillna(0.0).values
        scores_gkp = cos_sim_sklearn(
            X_gkp, pfa_gkp_vector.reshape(1, -1)
        ).flatten()
        df_maroc.loc[mask_gkp, "score_holdout"] = scores_gkp
        df_maroc.loc[mask_gkp, "score_complet"] = scores_gkp
        sp(f"\n    Score PFA gardiens recalcule (vecteur GKP) OK")

    # Composition avec modele holdout
    sp("\n[4] Composition avec modele holdout (sans avoir vu le Maroc)...")

    # Filtre joueurs retirés
    EXCLUSIONS = ["y. belhanda", "f. fajr", "k. boutaib", "m. boussoufa"]
    if "short_name" in df_maroc.columns:
        df_maroc = df_maroc[
            ~df_maroc["short_name"].str.lower().isin(EXCLUSIONS)
        ]

    FORMATION = {"GKP":1, "DEF":4, "MIL":3, "ATT":3}
    LABELS    = {"GKP":"Gardien","DEF":"Defenseurs","MIL":"Milieux","ATT":"Attaquants"}

    if "poste" in df_maroc.columns:
        comp_ho = []
        for poste, nb in FORMATION.items():
            pool = df_maroc[df_maroc["poste"]==poste].nlargest(nb*3,"score_holdout")
            if len(pool) == 0:
                continue
            comp_ho.append(pool.head(nb))

        if comp_ho:
            df_c = pd.concat(comp_ho).reset_index(drop=True)
            sep = "=" * 60
            sp(f"\n{sep}")
            sp("  COMPOSITION HOLDOUT (generalisation sans Maroc)")
            sp(sep)
            for poste in ["GKP","DEF","MIL","ATT"]:
                g = df_c[df_c["poste"]==poste]
                if len(g)==0:
                    continue
                sp(f"\n  {LABELS[poste]} :")
                for _, row in g.iterrows():
                    nom   = str(row.get("short_name","?")).encode("ascii","replace").decode("ascii")
                    s_ho  = row.get("score_holdout", 0)
                    s_comp= row.get("score_complet", 0)
                    sp(f"    {nom:28s}  holdout={s_ho:.4f}  complet={s_comp:.4f}")
else:
    maroc_mask = np.zeros(len(df_players), dtype=bool)
    df_maroc   = pd.DataFrame()

# ── Test sur ensemble de validation ─────────────────────────────────
sp("\n[5] Test sur validation (20% hors loss d'entrainement)...")

try:
    masks    = torch.load("split_masks.pt", weights_only=True)
    val_mask = masks["val_mask"].numpy()
except FileNotFoundError:
    n = data.x.shape[0]
    np.random.seed(42)
    perm = np.random.permutation(n)
    val_mask = np.zeros(n, dtype=bool)
    val_mask[perm[int(0.8*n):]] = True

y_true_val = y_true[val_mask]
y_ho_val   = sc_holdout[val_mask]
y_comp_val = sc_complet[val_mask]

sp(f"    Joueurs en validation : {val_mask.sum():,}")
sp(f"\n    {'Metrique':<20} {'Modele holdout':>16} {'Modele complet':>16}")
sp(f"    {'-'*55}")
sp(f"    {'MAE':<20} {mean_absolute_error(y_true_val,y_ho_val):>16.4f}"
   f" {mean_absolute_error(y_true_val,y_comp_val):>16.4f}")
sp(f"    {'R2':<20} {r2_score(y_true_val,y_ho_val):>16.4f}"
   f" {r2_score(y_true_val,y_comp_val):>16.4f}")
sp(f"    {'RMSE':<20} {np.sqrt(mean_squared_error(y_true_val,y_ho_val)):>16.4f}"
   f" {np.sqrt(mean_squared_error(y_true_val,y_comp_val)):>16.4f}")

# ── Sauvegarde ──────────────────────────────────────────────────────
sp("\n[6] Sauvegarde...")

if len(df_maroc) > 0:
    cols_save = [c for c in ["short_name","poste","club_name","nationality_name",
                              "overall","overall_raw","score_holdout","score_complet",
                              "pfa_true"] if c in df_maroc.columns]
    df_maroc[cols_save].sort_values("score_holdout", ascending=False)\
        .to_csv("resultats_jamais_vus.csv", index=False, encoding="utf-8")
    sp(f"    resultats_jamais_vus.csv -> {len(df_maroc)} joueurs marocains")

sep = "=" * 58
sp(f"\n{sep}")
sp("  TEST TERMINE")
sp(sep)
sp("  resultats_jamais_vus.csv -> scores joueurs marocains")
sp("  (modele entraine sans les voir une seule fois)")
sp(sep)