"""
=============================================================
construction_graphe.py — Construction du graphe GNN
=============================================================
CORRECTIONS APPORTÉES :
  1. Fuzzy matching amélioré (rapidfuzz) pour FIFA ↔ StatsBomb
  2. Correction de la classification des postes (Munir, etc.)
  3. Validation manuelle des joueurs marocains clés
  4. ✅ PRIORITÉ 2 : Arêtes synthétiques pour les Marocains isolés
     (les 84 Marocains sans arêtes StatsBomb reçoivent des arêtes
      basées sur la similarité cosinus de leurs features FIFA)
=============================================================
Entrée  : dataset_gnn/players_all_clean.csv
          players_statsbomb.csv
          interactions.csv
Sortie  : graph_data.pt   (x, edge_index, edge_attr, y, overall)
          players_final.csv
          pfa_vector.json
=============================================================
"""

import pandas as pd
import numpy as np
import json, warnings
warnings.filterwarnings("ignore")

print("=" * 55)
print("  CONSTRUCTION DU GRAPHE GNN")
print("=" * 55)

import os
from sklearn.preprocessing import MinMaxScaler

# ─────────────────────────────────────────────
# ETAPE 1 — CHARGER LES FICHIERS
# ─────────────────────────────────────────────
print("\n[1] Chargement des fichiers...")

if os.path.exists("dataset_gnn/players_all_clean.csv"):
    df_fifa = pd.read_csv("dataset_gnn/players_all_clean.csv", encoding="utf-8")
    print(f"    FIFA (nettoyé)  : {len(df_fifa):,} joueurs")
else:
    print("    ERREUR : dataset_gnn/players_all_clean.csv introuvable.")
    print("    Lancez d'abord : python script.py")
    exit(1)

df_statsbomb = pd.read_csv("players_statsbomb.csv", encoding="utf-8")
df_edges     = pd.read_csv("interactions.csv",      encoding="utf-8")

print(f"    StatsBomb       : {len(df_statsbomb):,} joueurs")
print(f"    Interactions    : {len(df_edges):,} arêtes")

# ─────────────────────────────────────────────
# CORRECTION 1 — CLASSIFICATION DES POSTES
# ─────────────────────────────────────────────
CORRECTIONS_POSTES = {
    "munir"            : "ATT",
    "m. el haddadi"    : "ATT",
    "munir el haddadi" : "ATT",
}

if "poste" in df_fifa.columns:
    for nom, poste_corrige in CORRECTIONS_POSTES.items():
        mask = df_fifa["short_name"].str.lower().str.contains(nom, na=False)
        nb = mask.sum()
        if nb > 0:
            df_fifa.loc[mask, "poste"] = poste_corrige
            print(f"    [CORRECTION POSTE] {nom} -> {poste_corrige} ({nb} joueur(s))")

# ─────────────────────────────────────────────
# ETAPE 2 — MATCHING FIFA ↔ STATSBOMB (FUZZY)
# ─────────────────────────────────────────────
print("\n[2] Matching des noms FIFA <-> StatsBomb (fuzzy matching)...")

def normalize_name(name):
    if pd.isna(name):
        return ""
    name = str(name).lower().strip()
    for k, v in {
        'é':'e','è':'e','ê':'e','ë':'e',
        'à':'a','â':'a','ä':'a',
        'î':'i','ï':'i','í':'i',
        'ô':'o','ö':'o','ó':'o',
        'ù':'u','û':'u','ü':'u','ú':'u',
        'ç':'c','ñ':'n','ć':'c','č':'c',
        'š':'s','ž':'z','ř':'r','ń':'n',
        'ā':'a','ē':'e','ī':'i','ō':'o','ū':'u',
    }.items():
        name = name.replace(k, v)
    return name

MAPPING_MANUEL = {
    "sofyan amrabat"          : "s. amrabat",
    "yassine bounou"          : "y. bounou",
    "achraf hakimi mouh"      : "a. hakimi",
    "achraf hakimi"           : "a. hakimi",
    "hakim ziyech"            : "h. ziyech",
    "youssef en-nesyri"       : "y. en-nesyri",
    "noussair mazraoui"       : "n. mazraoui",
    "azzedine ounahi"         : "a. ounahi",
    "sofiane boufal"          : "s. boufal",
    "romain saiss"            : "r. saiss",
    "nayef aguerd"            : "n. aguerd",
    "ilias chair"             : "i. chair",
    "zakaria aboukhlal"       : "z. aboukhlal",
    "abdelhamid sabiri"       : "a. sabiri",
    "selim amallah"           : "s. amallah",
    "amine harit"             : "a. harit",
    "jawad el yamiq"          : "j. el yamiq",
    "yahia attiat-allah"      : "y. attiat-allah",
    "munir el haddadi"        : "munir",
}

df_fifa["name_norm"]       = df_fifa["short_name"].apply(normalize_name)
df_statsbomb["name_norm"]  = df_statsbomb["short_name"].apply(normalize_name)
name_to_id = dict(zip(df_fifa["name_norm"], df_fifa["player_id"]))

def statsbomb_to_fifa_candidates(full_name_norm):
    parts = full_name_norm.split()
    if not parts:
        return []
    initial = parts[0][0] + "."
    candidates = [f"{initial} {word}" for word in parts[1:] if len(word) > 1]
    candidates.append(full_name_norm)
    return candidates

try:
    from rapidfuzz import process, fuzz
    FUZZY_AVAILABLE = True
    print("    rapidfuzz disponible -> fuzzy matching activé")
except ImportError:
    FUZZY_AVAILABLE = False
    print("    [!] rapidfuzz non installé -> pip install rapidfuzz")

fifa_names_list = list(name_to_id.keys())

def fuzzy_match_name(sb_name_norm, threshold=82):
    if sb_name_norm in MAPPING_MANUEL:
        fifa_short = MAPPING_MANUEL[sb_name_norm]
        if fifa_short in name_to_id:
            return name_to_id[fifa_short]
    if sb_name_norm in name_to_id:
        return name_to_id[sb_name_norm]
    for cand in statsbomb_to_fifa_candidates(sb_name_norm):
        if cand in name_to_id:
            return name_to_id[cand]
    if FUZZY_AVAILABLE:
        result = process.extractOne(
            sb_name_norm, fifa_names_list,
            scorer=fuzz.token_sort_ratio, score_cutoff=threshold
        )
        if result:
            matched_name, score, _ = result
            return name_to_id[matched_name]
    return None

sb_to_fifa = {}
for _, row in df_statsbomb.iterrows():
    fifa_id = fuzzy_match_name(row["name_norm"])
    if fifa_id is not None:
        sb_to_fifa[row["name_norm"]] = fifa_id

print(f"    Joueurs StatsBomb matchés : {len(sb_to_fifa)} / {len(df_statsbomb)}")

print("\n    Vérification des joueurs marocains clés :")
joueurs_cles = [
    "sofyan amrabat", "yassine bounou", "achraf hakimi mouh",
    "hakim ziyech", "youssef en-nesyri", "noussair mazraoui",
    "azzedine ounahi", "sofiane boufal", "romain saiss"
]
for nom in joueurs_cles:
    status = "✓ MATCHÉ" if nom in sb_to_fifa else "✗ ABSENT"
    print(f"      {status} : {nom}")

SB_COLS = ["pass_accuracy", "duel_win_rate", "pressings", "carries", "goal_ratio"]

df_sb_mapped = df_statsbomb.copy()
df_sb_mapped["player_id"] = df_sb_mapped["name_norm"].map(sb_to_fifa)
df_sb_mapped = df_sb_mapped.dropna(subset=["player_id"])
df_sb_mapped["player_id"] = df_sb_mapped["player_id"].astype(int)

df_players = df_fifa.merge(
    df_sb_mapped[["player_id"] + SB_COLS],
    on="player_id", how="left"
)

for col in SB_COLS:
    if col in df_players.columns:
        col_max = df_players[col].max()
        if col_max > 0:
            df_players[col] = df_players[col] / col_max
        df_players[col] = df_players[col].fillna(0.0)

# ─────────────────────────────────────────────
# ÉTAPE 2b — IMPUTATION des zéros StatsBomb
# Les joueurs sans données réelles reçoivent la
# moyenne de leur poste (calculée sur les joueurs
# qui ont de vraies stats StatsBomb).
# Cela évite de pénaliser injustement 81-94 % du corpus.
# ─────────────────────────────────────────────
print("\n[2b] Imputation des zéros StatsBomb par moyenne de poste...")

for col in SB_COLS:
    if col not in df_players.columns:
        continue
    n_zeros_avant = (df_players[col] == 0).sum()
    for poste in ['GKP', 'DEF', 'MIL', 'ATT']:
        mask_poste = df_players['poste'] == poste
        mask_real  = mask_poste & (df_players[col] > 0)
        n_real     = mask_real.sum()
        if n_real >= 5:
            mean_val = round(float(df_players.loc[mask_real, col].mean()), 4)
        else:
            # Pas assez de données réelles pour ce poste
            mean_val = 0.04 if poste == 'GKP' else 0.10
        mask_zero = mask_poste & (df_players[col] == 0)
        df_players.loc[mask_zero, col] = mean_val
    n_zeros_apres = (df_players[col] == 0).sum()
    print(f"    {col:30s}: {n_zeros_avant:5,} zéros -> {n_zeros_apres:3,} zéros restants")

matched_sb = (df_players[SB_COLS[0]] > 0).sum()
print(f"\n    Joueurs avec stats StatsBomb : {matched_sb}")

df_players = df_players.reset_index(drop=True)
df_players["player_id"] = df_players.index

maroc_df = df_players[df_players["is_moroccan"] == 1]
maroc_avec_sb = (maroc_df[SB_COLS[0]] > 0).sum()
print(f"    Marocains avec stats StatsBomb : {maroc_avec_sb} / {len(maroc_df)}")

# ─────────────────────────────────────────────
# ETAPE 3 — FEATURES DES NŒUDS
# ─────────────────────────────────────────────
print("\n[3] Sélection des features...")

FIFA_FEATURES = [
    "pace", "shooting", "passing", "dribbling",
    "defending", "physic", "power_stamina", "mentality_interceptions",
    "goalkeeping_diving", "goalkeeping_handling",
    "goalkeeping_kicking", "goalkeeping_positioning", "goalkeeping_reflexes",
]
FIFA_FEATURES = [c for c in FIFA_FEATURES if c in df_players.columns]
SB_FEATURES   = [c for c in SB_COLS if c in df_players.columns]
ALL_FEATURES  = FIFA_FEATURES + SB_FEATURES

X = df_players[ALL_FEATURES].fillna(0.0).values
print(f"    Features : {ALL_FEATURES}")
print(f"    Matrice X : {X.shape}")

overall_vals = df_players["overall"].fillna(0.0).values
print(f"    Overall (target) : min={overall_vals.min():.3f} max={overall_vals.max():.3f}")

# ─────────────────────────────────────────────
# ETAPE 4 — ARÊTES RÉELLES (StatsBomb)
# ─────────────────────────────────────────────
print("\n[4] Construction des arêtes réelles...")

df_edges["a_norm"] = df_edges["joueur_a"].apply(normalize_name)
df_edges["b_norm"] = df_edges["joueur_b"].apply(normalize_name)

full_name_to_id = dict(zip(df_fifa["name_norm"], df_fifa["player_id"]))

def resolve_interaction_name(name_norm):
    if name_norm in MAPPING_MANUEL:
        fifa_short = MAPPING_MANUEL[name_norm]
        if fifa_short in name_to_id:
            return name_to_id[fifa_short]
    if name_norm in full_name_to_id:
        return full_name_to_id[name_norm]
    if name_norm in sb_to_fifa:
        return sb_to_fifa[name_norm]
    for cand in statsbomb_to_fifa_candidates(name_norm):
        if cand in full_name_to_id:
            return full_name_to_id[cand]
    return None

df_edges["a_id"] = df_edges["a_norm"].apply(resolve_interaction_name)
df_edges["b_id"] = df_edges["b_norm"].apply(resolve_interaction_name)

df_mapped = df_edges.dropna(subset=["a_id", "b_id"]).copy()
df_mapped["a_id"] = df_mapped["a_id"].astype(int)
df_mapped["b_id"] = df_mapped["b_id"].astype(int)

n = len(df_players)
df_mapped = df_mapped[
    (df_mapped["a_id"] < n) & (df_mapped["b_id"] < n) &
    (df_mapped["a_id"] != df_mapped["b_id"])
]

print(f"    Arêtes matchées (interactions réelles) : {len(df_mapped):,} / {len(df_edges):,}")

maroc_ids = set(df_players[df_players["is_moroccan"] == 1]["player_id"].tolist())
aretes_maroc = df_mapped[
    df_mapped["a_id"].isin(maroc_ids) | df_mapped["b_id"].isin(maroc_ids)
]
print(f"    Arêtes impliquant un Marocain : {len(aretes_maroc):,}")

if "poids" not in df_mapped.columns:
    df_mapped = df_mapped.copy()
    df_mapped["poids"] = df_mapped.get("nb_passes", pd.Series(1, index=df_mapped.index))
    poids_max = df_mapped["poids"].max()
    if poids_max > 0:
        df_mapped["poids"] = df_mapped["poids"] / poids_max
df_mapped["poids"] = df_mapped["poids"].fillna(0.5).clip(0, 1)

# ─────────────────────────────────────────────
# ETAPE 5 — ✅ PRIORITÉ 2 : ARÊTES SYNTHÉTIQUES
#            pour les Marocains isolés (sans arêtes StatsBomb)
# ─────────────────────────────────────────────
print("\n[5] Arêtes synthétiques pour les Marocains isolés...")

from sklearn.metrics.pairwise import cosine_similarity as cos_sim

# Identifier les Marocains isolés (degré = 0 dans le graphe réel)
edges_set = set(df_mapped["a_id"].tolist() + df_mapped["b_id"].tolist())
maroc_isoles = [
    idx for idx in maroc_ids
    if idx not in edges_set and idx < n
]
print(f"    Marocains avec arêtes réelles  : {len(maroc_ids) - len(maroc_isoles)}")
print(f"    Marocains isolés (sans arêtes) : {len(maroc_isoles)}")

synth_edges = []

if len(maroc_isoles) > 0:
    K = 5  # nombre de voisins synthétiques par joueur isolé

    for idx in maroc_isoles:
        # Features du joueur marocain isolé
        feat_joueur = X[idx].reshape(1, -1)

        # Calculer similarité avec tous les autres joueurs
        # (on prend un sous-ensemble pour la performance)
        # Priorité : autres Marocains d'abord, puis meilleurs FIFA
        autres_maroc = [i for i in maroc_ids if i != idx and i < n]
        top_fifa_idx = np.argsort(overall_vals)[-500:][::-1].tolist()
        candidats = list(set(autres_maroc + top_fifa_idx))
        candidats = [c for c in candidats if c < n]

        if len(candidats) == 0:
            continue

        feat_candidats = X[candidats]
        sims = cos_sim(feat_joueur, feat_candidats)[0]

        # Prendre les K plus similaires
        top_k_idx = np.argsort(sims)[-K:][::-1]
        for ki in top_k_idx:
            voisin = candidats[ki]
            poids_synth = float(sims[ki])
            if poids_synth > 0.5:  # seuil minimal de similarité
                synth_edges.append({
                    "a_id": idx,
                    "b_id": voisin,
                    "poids": round(poids_synth, 4)
                })

    df_synth = pd.DataFrame(synth_edges)
    if len(df_synth) > 0:
        df_mapped = pd.concat(
            [df_mapped[["a_id", "b_id", "poids"]], df_synth],
            ignore_index=True
        )
        print(f"    Arêtes synthétiques ajoutées   : {len(df_synth):,}")
        print(f"    Total arêtes après synthèse    : {len(df_mapped):,}")

        # Vérification : Marocains maintenant connectés
        edges_set_apres = set(df_mapped["a_id"].tolist() + df_mapped["b_id"].tolist())
        maroc_connectes = sum(1 for idx in maroc_ids if idx in edges_set_apres)
        print(f"    Marocains connectés au graphe  : {maroc_connectes} / {len(maroc_ids)} ✅")
    else:
        print("    [!] Aucune arête synthétique générée (seuil similarité trop élevé)")
else:
    print("    Tous les Marocains ont déjà des arêtes réelles ✅")

# ─────────────────────────────────────────────
# ETAPE 6 — VECTEUR PFA (profil idéal)
# ─────────────────────────────────────────────
print("\n[6] Construction du vecteur PFA...")

pfa_values = {
    "pace": 0.80, "shooting": 0.70, "passing": 0.82,
    "dribbling": 0.78, "defending": 0.72, "physic": 0.80,
    "power_stamina": 0.88, "mentality_interceptions": 0.78,
    "goalkeeping_diving": 0.85,
"goalkeeping_handling": 0.82,
"goalkeeping_kicking": 0.78,
"goalkeeping_positioning": 0.83,
"goalkeeping_reflexes": 0.87,
    "pass_accuracy": 0.85, "duel_win_rate": 0.70,
    "pressings": 0.88, "carries": 0.80, "goal_ratio": 0.72,
}
pfa_dict   = {k: pfa_values.get(k, 0.5) for k in ALL_FEATURES}
pfa_vector = np.array(list(pfa_dict.values()))

with open("pfa_vector.json", "w", encoding="utf-8") as f:
    json.dump(pfa_dict, f, indent=2)
print(f"    Vecteur PFA : {len(pfa_vector)} dimensions -> pfa_vector.json")

# ─────────────────────────────────────────────
# ETAPE 7 — SAUVEGARDE players_final.csv
# ─────────────────────────────────────────────
print("\n[7] Sauvegarde players_final.csv...")
df_players.to_csv("players_final.csv", index=False, encoding="utf-8")
print(f"    {len(df_players):,} joueurs -> players_final.csv")
print(f"    Marocains : {(df_players['is_moroccan']==1).sum()}")

if "poste" in df_players.columns:
    dist = df_players[df_players["is_moroccan"]==1]["poste"].value_counts().to_dict()
    print(f"    Postes marocains : {dist}")

# ─────────────────────────────────────────────
# ETAPE 8 — CONSTRUCTION DU GRAPHE PyTorch
# ─────────────────────────────────────────────
print("\n[8] Construction du graphe PyTorch Geometric...")

try:
    import torch
    from torch_geometric.data import Data

    x            = torch.tensor(X, dtype=torch.float)
    src          = torch.tensor(df_mapped["a_id"].values, dtype=torch.long)
    dst          = torch.tensor(df_mapped["b_id"].values, dtype=torch.long)
    edge_index   = torch.cat([torch.stack([src, dst], dim=0),
                               torch.stack([dst, src], dim=0)], dim=1)
    w            = torch.tensor(df_mapped["poids"].values, dtype=torch.float)
    edge_attr    = torch.cat([w, w], dim=0).unsqueeze(1)
    pfa_tensor   = torch.tensor(pfa_vector, dtype=torch.float)
    y            = torch.cosine_similarity(
                       x, pfa_tensor.unsqueeze(0).expand(x.size(0), -1)
                   )
    overall_tensor = torch.tensor(overall_vals, dtype=torch.float)

    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr,
                y=y, overall=overall_tensor)
    torch.save(data, "graph_data.pt")

    print(f"    Nœuds      : {data.x.shape[0]:,}")
    print(f"    Features   : {data.x.shape[1]}")
    print(f"    Arêtes     : {data.edge_index.shape[1]:,}")
    print(f"    y (PFA sim): min={data.y.min():.3f} max={data.y.max():.3f}")
    print(f"    overall    : min={data.overall.min():.3f} max={data.overall.max():.3f}")
    print(f"    graph_data.pt sauvegardé [OK]")

except ImportError:
    print("    [!] PyTorch non installé -> pip install torch torch_geometric")

# ─────────────────────────────────────────────
# RÉSUMÉ
# ─────────────────────────────────────────────
print(f"\n{'='*55}")
print("  TERMINÉ")
print(f"{'='*55}")
print(f"  players_final.csv -> {len(df_players):,} joueurs")
print(f"  pfa_vector.json   -> {len(ALL_FEATURES)} dimensions")
print(f"  graph_data.pt     -> prêt pour GNN [OK]")
print(f"{'='*55}")
print(f"\n-> Étape suivante : python entrainement_gnn.py")