"""
=============================================================
entrainement_gnn.py — Entraînement supervisé du GNN
=============================================================
Entrée  : graph_data.pt           (x, edge_index, y, overall)
          players_final.csv
Sortie  : gnn_model.pt            (meilleur modèle)
          gnn_model_holdout.pt    (modèle sans joueurs marocains)
          composition_finale.csv  (11 meilleurs marocains)
=============================================================
Architecture : GraphSAGE 3 couches + BatchNorm + tête de prédiction
Objectif     : Prédire la similarité PFA [0, 1]
               (compatibilité du joueur avec le style de jeu marocain)
=============================================================
"""

import os
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv
import pandas as pd
import numpy as np
import json, warnings
warnings.filterwarnings("ignore")

print("=" * 55)
print("  ENTRAÎNEMENT DU GNN (supervisé)")
print("=" * 55)

# ---------------------------------------------
# ETAPE 1 — CHARGER LE GRAPHE
# ---------------------------------------------
print("\n[1] Chargement du graphe...")

data = torch.load("graph_data.pt", weights_only=False)
print(f"    Nœuds     : {data.x.shape[0]:,}")
print(f"    Features  : {data.x.shape[1]}")
print(f"    Arêtes    : {data.edge_index.shape[1]:,}")

# ✅ MODIFICATION PRINCIPALE :
# Target = similarité PFA directement (data.y)
# On n'utilise PLUS data.overall (FIFA)
# car l'objectif est de mesurer la compatibilité
# avec le style de jeu marocain, pas la cote FIFA.
y_raw = data.y
print(f"    Target    : similarité PFA [OK]")
print(f"    y range   : min={y_raw.min():.3f} max={y_raw.max():.3f}")

# data.y est déjà dans [0, 0.944] — pas besoin de renormaliser
y = y_raw

IN_DIM = data.x.shape[1]
HIDDEN = 128
OUT_DIM = 64
EPOCHS = 300
LR = 0.005
PATIENCE = 40  # early stopping

# ---------------------------------------------
# ETAPE 2 — ARCHITECTURE GNN
# ---------------------------------------------
print(f"\n[2] Architecture GNN...")

class GNN(nn.Module):
    """
    GraphSAGE 3 couches avec BatchNorm et tête de régression.
    Agrège l'information du voisinage pour contextualiser la compatibilité
    de chaque joueur avec le projet de jeu marocain (PFA).
    """
    def __init__(self, in_dim, hidden, out_dim):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden)
        self.bn1   = nn.BatchNorm1d(hidden)
        self.conv2 = SAGEConv(hidden, hidden)
        self.bn2   = nn.BatchNorm1d(hidden)
        self.conv3 = SAGEConv(hidden, out_dim)
        self.bn3   = nn.BatchNorm1d(out_dim)
        # Tête de prédiction : embedding -> score scalaire [0, 1]
        self.head  = nn.Sequential(
            nn.Linear(out_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def encode(self, x, edge_index):
        """Génère les embeddings joueurs"""
        x = self.bn1(F.relu(self.conv1(x, edge_index)))
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.bn2(F.relu(self.conv2(x, edge_index)))
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.bn3(self.conv3(x, edge_index))
        return x

    def forward(self, x, edge_index):
        emb  = self.encode(x, edge_index)
        pred = self.head(emb).squeeze(-1)
        return emb, pred

model     = GNN(IN_DIM, HIDDEN, OUT_DIM)
optimizer = torch.optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode="min", factor=0.5, patience=20, min_lr=1e-5
)

n_params = sum(p.numel() for p in model.parameters())
print(f"    in_dim    : {IN_DIM}")
print(f"    hidden    : {HIDDEN}")
print(f"    out_dim   : {OUT_DIM}")
print(f"    params    : {n_params:,}")
print(f"    epochs    : {EPOCHS} (early stopping patience={PATIENCE})")

# ---------------------------------------------
# ETAPE 3 — SPLIT TRAIN / VALIDATION
# ---------------------------------------------
print(f"\n[3] Split Train/Validation (80/20)...")

n = data.x.shape[0]
torch.manual_seed(42)
perm = torch.randperm(n)
split = int(0.8 * n)

train_mask = torch.zeros(n, dtype=torch.bool)
val_mask   = torch.zeros(n, dtype=torch.bool)
train_mask[perm[:split]]  = True
val_mask[perm[split:]]    = True

print(f"    Train : {train_mask.sum():,} joueurs")
print(f"    Val   : {val_mask.sum():,} joueurs")

# Sauvegarder les masques pour test_donnees_jamais_vues.py
torch.save({"train_mask": train_mask, "val_mask": val_mask, "perm": perm},
           "split_masks.pt")

# ---------------------------------------------
# ETAPE 4 — ENTRAÎNEMENT (modèle complet)
# ---------------------------------------------
print(f"\n[4] Entraînement sur tous les joueurs...")
print(f"    {'Epoch':>6} | {'Loss Train':>10} | {'Loss Val':>10} | {'Statut'}")
print(f"    {'-'*52}")

best_val_loss  = float("inf")
patience_count = 0
history = []

for epoch in range(1, EPOCHS + 1):
    # --- Forward train ---
    model.train()
    optimizer.zero_grad()
    _, pred = model(data.x, data.edge_index)
    loss_train = F.mse_loss(pred[train_mask], y[train_mask])
    loss_train.backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
    optimizer.step()

    # --- Forward validation ---
    model.eval()
    with torch.no_grad():
        _, pred_val = model(data.x, data.edge_index)
        loss_val = F.mse_loss(pred_val[val_mask], y[val_mask])

    scheduler.step(loss_val)
    history.append((loss_train.item(), loss_val.item()))

    # Meilleur modèle sur validation
    statut = ""
    if loss_val.item() < best_val_loss:
        best_val_loss  = loss_val.item()
        patience_count = 0
        torch.save(model.state_dict(), "gnn_model.pt")
        statut = "[OK] sauvegardé"
    else:
        patience_count += 1

    if epoch % 25 == 0 or epoch == 1:
        print(f"    {epoch:>6} | {loss_train.item():>10.6f} | {loss_val.item():>10.6f} | {statut}")

    # Early stopping
    if patience_count >= PATIENCE:
        print(f"\n    Early stopping à l'epoch {epoch} (patience={PATIENCE} atteinte)")
        break

print(f"\n    Meilleur loss val : {best_val_loss:.6f}")
print(f"    Modèle sauvegardé : gnn_model.pt [OK]")

# ---------------------------------------------
# ETAPE 5 — MODÈLE HOLDOUT (sans les marocains)
# ---------------------------------------------
print(f"\n[5] Entraînement du modèle holdout (Maroc exclu)...")

if os.path.exists("players_final.csv"):
    _df_ho = pd.read_csv("players_final.csv", encoding="utf-8")
    if "is_moroccan" not in _df_ho.columns:
        _df_ho["is_moroccan"] = 0
    maroc_mask_np = _df_ho["is_moroccan"].values == 1
else:
    print("    [!] players_final.csv absent -> masque marocain approximatif")
    maroc_mask_np = np.zeros(n, dtype=bool)

maroc_mask = torch.tensor(maroc_mask_np, dtype=torch.bool)
non_maroc  = ~maroc_mask

print(f"    Joueurs marocains (exclus) : {maroc_mask.sum().item()}")
print(f"    Joueurs non-marocains (train): {non_maroc.sum().item():,}")

model_holdout = GNN(IN_DIM, HIDDEN, OUT_DIM)
opt_ho = torch.optim.Adam(model_holdout.parameters(), lr=LR, weight_decay=1e-4)
sched_ho = torch.optim.lr_scheduler.ReduceLROnPlateau(
    opt_ho, mode="min", factor=0.5, patience=20, min_lr=1e-5
)

# Split sur joueurs non-marocains
non_maroc_idx  = torch.where(non_maroc)[0]
n_nm           = len(non_maroc_idx)
perm_nm        = torch.randperm(n_nm, generator=torch.Generator().manual_seed(42))
split_nm       = int(0.85 * n_nm)
train_nm       = torch.zeros(n, dtype=torch.bool)
val_nm         = torch.zeros(n, dtype=torch.bool)
train_nm[non_maroc_idx[perm_nm[:split_nm]]] = True
val_nm[non_maroc_idx[perm_nm[split_nm:]]]   = True

best_ho_val   = float("inf")
patience_ho   = 0

for epoch in range(1, EPOCHS + 1):
    model_holdout.train()
    opt_ho.zero_grad()
    _, pred_ho = model_holdout(data.x, data.edge_index)
    loss_ho = F.mse_loss(pred_ho[train_nm], y[train_nm])
    loss_ho.backward()
    torch.nn.utils.clip_grad_norm_(model_holdout.parameters(), max_norm=1.0)
    opt_ho.step()

    model_holdout.eval()
    with torch.no_grad():
        _, pred_ho_val = model_holdout(data.x, data.edge_index)
        val_ho = F.mse_loss(pred_ho_val[val_nm], y[val_nm])

    sched_ho.step(val_ho)

    if val_ho.item() < best_ho_val:
        best_ho_val = val_ho.item()
        patience_ho = 0
        torch.save(model_holdout.state_dict(), "gnn_model_holdout.pt")
    else:
        patience_ho += 1

    if patience_ho >= PATIENCE:
        print(f"    Early stopping holdout epoch {epoch}")
        break

print(f"    Meilleur loss holdout val : {best_ho_val:.6f}")
print(f"    Modèle sauvegardé : gnn_model_holdout.pt [OK]")

# ---------------------------------------------
# ETAPE 6 — GÉNÉRATION DES SCORES PFA
# ---------------------------------------------
print(f"\n[6] Génération des scores PFA...")

model.load_state_dict(torch.load("gnn_model.pt", weights_only=True))
model.eval()

with torch.no_grad():
    embeddings, scores_tensor = model(data.x, data.edge_index)

scores = scores_tensor.numpy()

print(f"    Score min  : {scores.min():.4f}")
print(f"    Score max  : {scores.max():.4f}")
print(f"    Score moy  : {scores.mean():.4f}")

# ---------------------------------------------
# ETAPE 7 — COMPOSITION OPTIMALE MAROC
# ---------------------------------------------
print(f"\n[7] Sélection de la composition optimale (4-3-3)...")

if not os.path.exists("players_final.csv"):
    print("    [!] players_final.csv absent -> lance construction_graphe.py d'abord")
    df_players = None
else:
    df_players = pd.read_csv("players_final.csv", encoding="utf-8")
    df_players["pfa_score"] = scores
    if "is_moroccan" not in df_players.columns:
        df_players["is_moroccan"] = 0

    # ✅ CORRECTION GARDIEN — vecteur PFA spécifique GKP
    # Le vecteur PFA général est orienté champ (pressing, passes...)
    # ce qui donne un score anormalement bas aux gardiens.
    # On recalcule un score PFA dédié pour les gardiens.
    ALL_FEATURES = ['pace', 'shooting', 'passing', 'dribbling', 'defending',
                    'physic', 'power_stamina', 'mentality_interceptions',
                    'goalkeeping_diving', 'goalkeeping_handling',
                    'goalkeeping_kicking', 'goalkeeping_positioning',
                    'goalkeeping_reflexes', 'pass_accuracy', 'duel_win_rate',
                    'pressings', 'carries', 'goal_ratio']
    ALL_FEATURES = [f for f in ALL_FEATURES if f in df_players.columns]

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

    from sklearn.metrics.pairwise import cosine_similarity as cos_sim_sklearn
    mask_gkp = df_players["poste"] == "GKP"
    if mask_gkp.sum() > 0:
        X_gkp = df_players.loc[mask_gkp, ALL_FEATURES].fillna(0.0).values
        scores_gkp = cos_sim_sklearn(
            X_gkp, pfa_gkp_vector.reshape(1, -1)
        ).flatten()
        df_players.loc[mask_gkp, "pfa_score"] = scores_gkp
        print(f"    Score PFA gardiens recalculé (vecteur GKP) ✅")
        # Afficher Bounou pour vérification
        bounou = df_players[df_players["short_name"].str.contains("Bounou", na=False)]
        if len(bounou) > 0:
            print(f"    Bounou pfa_score : {bounou['pfa_score'].values[0]:.4f}")

if df_players is None:
    print("    [!] Composition ignorée — players_final.csv manquant")
    df_maroc = pd.DataFrame()
else:
    df_maroc = df_players[df_players["is_moroccan"] == 1].copy()
    # Filtre : exclure joueurs retirés de la sélection nationale
    print(df_maroc[df_maroc["short_name"].str.contains("Mazraoui", na=False)][["short_name","poste","pfa_score"]])
    EXCLUSIONS = ["y. belhanda", "f. fajr", "k. boutaib", "m. boussoufa"]
    if "short_name" in df_maroc.columns:
        df_maroc = df_maroc[
            ~df_maroc["short_name"].str.lower().isin(EXCLUSIONS)
        ]
        print(f"    Joueurs exclus (retirés sélection) : {len(EXCLUSIONS)}")

if len(df_maroc) == 0:
    print("    [!] Aucun joueur marocain trouvé dans players_final.csv")
else:
    print(f"    Pool marocain : {len(df_maroc)} joueurs")

    # Formation 4-3-3
    FORMATION = {"GKP": 1, "DEF": 4, "MIL": 3, "ATT": 3}
    composition = []

    for poste, nb in FORMATION.items():
        pool = df_maroc[df_maroc["poste"] == poste].nlargest(nb * 3, "pfa_score")
        if len(pool) == 0:
            print(f"    [!] Aucun joueur marocain au poste {poste}")
            continue
        top = pool.head(nb)
        composition.append(top)

    if composition:
        df_compo = pd.concat(composition).reset_index(drop=True)

        print(f"\n{'='*58}")
        print(f"  COMPOSITION OPTIMALE — SÉLECTION NATIONALE MAROC")
        print(f"{'='*58}")

        LABELS = {"GKP": "Gardien", "DEF": "Défenseurs",
                  "MIL": "Milieux", "ATT": "Attaquants"}
        COLS_SHOW = [c for c in ["short_name", "poste", "club_name", "overall_raw", "pfa_score"]
                     if c in df_compo.columns]

        for poste in ["GKP", "DEF", "MIL", "ATT"]:
            groupe = df_compo[df_compo["poste"] == poste]
            if len(groupe) > 0:
                print(f"\n  {LABELS[poste]} :")
                for _, row in groupe.iterrows():
                    score = row.get("pfa_score", 0)
                    nom = row.get("short_name", "?")
                    overall_r = row.get("overall_raw", 0)
                    club = row.get("club_name", "?")
                    print(f"    • {nom:25s}  overall:{overall_r:>3.0f}  "
                          f"pfa:{score:.4f}  [{club}]")

        df_compo[COLS_SHOW].to_csv("composition_finale.csv", index=False, encoding="utf-8")
        print(f"\n{'='*58}")
        print(f"  composition_finale.csv -> {len(df_compo)} joueurs sélectionnés")

# ---------------------------------------------
# RESUME
# ---------------------------------------------
print(f"\n{'='*58}")
print(f"  ENTRAÎNEMENT TERMINÉ")
print(f"{'='*58}")
print(f"  gnn_model.pt         -> modèle (tous joueurs)")
print(f"  gnn_model_holdout.pt -> modèle (sans Maroc)")
print(f"  composition_finale.csv -> 11 joueurs sélectionnés")
print(f"{'='*58}")
print(f"\n-> Étapes suivantes :")
print(f"   python evaluation_gnn.py")
print(f"   python test_donnees_jamais_vues.py")