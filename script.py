"""
=============================================================
script.py — Nettoyage et préparation des données FIFA
=============================================================
Entrée  : players_24.csv (contient FIFA 15–23, ~10M lignes)
Sortie  : dataset_gnn/players_all_clean.csv
          dataset_gnn/players_maroc.csv
          dataset_gnn/config.json
=============================================================
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import json, os, warnings
warnings.filterwarnings("ignore")

print("=" * 55)
print("  NETTOYAGE DES DONNÉES FIFA")
print("=" * 55)

# ---------------------------------------------
# ETAPE 1 — CHARGER EN FILTRANT SUR FIFA 23
# ---------------------------------------------
print("\n[1] Chargement par chunks (FIFA 23 uniquement, evite les erreurs memoire)...")

COLS_NEEDED = [
    "fifa_version", "short_name", "nationality_name",
    "player_positions", "overall", "age", "league_name",
    "club_name", "pace", "shooting", "passing", "dribbling",
    "defending", "physic", "power_stamina", "mentality_interceptions",
    "international_reputation",
    "goalkeeping_diving", "goalkeeping_handling",
    "goalkeeping_kicking", "goalkeeping_positioning",
    "goalkeeping_reflexes",
]

# Lire en chunks pour eviter l'out-of-memory sur le fichier 5.6 GB
# On cherche d'abord la version max, puis on garde seulement cette version
chunks_all = []
latest_version = 0

print("    Passe 1 : detection de la version FIFA la plus recente...")
for chunk in pd.read_csv(
        "players_24.csv",
        usecols=["fifa_version"],
        encoding="utf-8",
        on_bad_lines="skip",
        chunksize=100_000,
        low_memory=False):
    v = int(chunk["fifa_version"].max())
    if v > latest_version:
        latest_version = v

print(f"    Version FIFA detectee : {latest_version}")
print("    Passe 2 : lecture des joueurs FIFA {}...".format(latest_version))

for chunk in pd.read_csv(
        "players_24.csv",
        usecols=COLS_NEEDED,
        encoding="utf-8",
        on_bad_lines="skip",
        chunksize=100_000,
        low_memory=False):
    sub = chunk[chunk["fifa_version"] == latest_version]
    if len(sub) > 0:
        chunks_all.append(sub)

df = pd.concat(chunks_all, ignore_index=True)
df = df.drop(columns=["fifa_version"])

print(f"    Joueurs      : {len(df):,}")

# ---------------------------------------------
# ETAPE 2 — GESTION DES POSTES
# ---------------------------------------------
print("\n[2] Encodage des postes...")

df["poste"] = df["player_positions"].str.split(",").str[0].str.strip()
df["poste"] = df["poste"].replace({
    "RW": "ATT", "LW": "ATT", "ST": "ATT", "CF": "ATT",
    "CAM": "MIL", "CM": "MIL", "CDM": "MIL",
    "RM": "MIL", "LM": "MIL",
    "CB": "DEF", "RB": "DEF", "LB": "DEF",
    "RWB": "DEF", "LWB": "DEF",
    "GK": "GKP",
})
df["poste"] = df["poste"].where(
    df["poste"].isin(["GKP", "DEF", "MIL", "ATT"]), "MIL"
)

print(f"    GKP:{(df['poste']=='GKP').sum()} | DEF:{(df['poste']=='DEF').sum()} | "
      f"MIL:{(df['poste']=='MIL').sum()} | ATT:{(df['poste']=='ATT').sum()}")

# ---------------------------------------------
# ETAPE 3 — VALEURS MANQUANTES
# ---------------------------------------------
print("\n[3] Gestion des valeurs manquantes...")

# Features de gardien : 0 pour les non-GK
GK_FEATURES = [
    "goalkeeping_diving", "goalkeeping_handling",
    "goalkeeping_kicking", "goalkeeping_positioning",
    "goalkeeping_reflexes",
]
for col in GK_FEATURES:
    if col in df.columns:
        df.loc[df["poste"] != "GKP", col] = 0.0
        df[col] = df[col].fillna(0.0)

# Features outfield : 0 pour les GK
OUTFIELD_FEATURES = [
    "pace", "shooting", "passing", "dribbling",
    "defending", "physic", "power_stamina", "mentality_interceptions",
]
for col in OUTFIELD_FEATURES:
    df.loc[df["poste"] == "GKP", col] = 0.0
    df[col] = df[col].fillna(df.groupby("poste")[col].transform("median"))
    df[col] = df[col].fillna(df[col].median())

# Overall, age, réputation
for col in ["overall", "age", "international_reputation"]:
    df[col] = df[col].fillna(df[col].median())

print(f"    Valeurs manquantes restantes : {df[OUTFIELD_FEATURES].isnull().sum().sum()}")

# ---------------------------------------------
# ETAPE 4 — DOUBLONS
# ---------------------------------------------
print("\n[4] Suppression des doublons...")

avant = len(df)
df = df.drop_duplicates(subset=["short_name", "nationality_name"])
df = df.reset_index(drop=True)
print(f"    Doublons supprimés : {avant - len(df)} | Restants : {len(df):,}")

# ---------------------------------------------
# ETAPE 5 — MARQUEUR MAROCAIN
# ---------------------------------------------
print("\n[5] Marquage des joueurs marocains...")

df["is_moroccan"] = (df["nationality_name"] == "Morocco").astype(int)
df_maroc_raw = df[df["is_moroccan"] == 1]
print(f"    Joueurs marocains : {len(df_maroc_raw)}")
print(f"    Postes : {df_maroc_raw['poste'].value_counts().to_dict()}")

# ---------------------------------------------
# ETAPE 6 — NORMALISATION MinMaxScaler [0, 1]
# ---------------------------------------------
print("\n[6] Normalisation MinMaxScaler [0, 1]...")

GNN_FEATURES = OUTFIELD_FEATURES + GK_FEATURES
CONTEXT_FEATURES = ["overall", "age", "international_reputation"]
ALL_NUMERIC = GNN_FEATURES + CONTEXT_FEATURES

# Garder overall_raw AVANT normalisation (pour supervision)
df["overall_raw"] = df["overall"].copy()

scaler = MinMaxScaler()
df[ALL_NUMERIC] = scaler.fit_transform(df[ALL_NUMERIC])

print(f"    Features normalisées : {len(ALL_NUMERIC)}")
print(f"    overall_raw (avant norm) : min={df['overall_raw'].min():.0f} max={df['overall_raw'].max():.0f}")
print(f"    overall (après norm)    : min={df['overall'].min():.3f} max={df['overall'].max():.3f}")

# ---------------------------------------------
# ETAPE 7 — SAUVEGARDE
# ---------------------------------------------
print("\n[7] Sauvegarde...")

os.makedirs("dataset_gnn", exist_ok=True)

df["player_id"] = df.index

COLS_OUT = (
    ["player_id", "short_name", "nationality_name",
     "poste", "club_name", "league_name", "is_moroccan", "overall_raw"]
    + GNN_FEATURES + CONTEXT_FEATURES
)

df[COLS_OUT].to_csv("dataset_gnn/players_all_clean.csv", index=False, encoding="utf-8")

df_maroc = df[df["is_moroccan"] == 1].copy()
df_maroc[COLS_OUT].to_csv("dataset_gnn/players_maroc.csv", index=False, encoding="utf-8")

config = {
    "fifa_version"     : latest_version,
    "gnn_features"     : GNN_FEATURES,
    "context_features" : CONTEXT_FEATURES,
    "n_total"          : len(df),
    "n_moroccan"       : int(df["is_moroccan"].sum()),
    "scaler_min"       : scaler.data_min_.tolist(),
    "scaler_max"       : scaler.data_max_.tolist(),
}
with open("dataset_gnn/config.json", "w", encoding="utf-8") as f:
    json.dump(config, f, indent=2)

# ---------------------------------------------
# RESUME
# ---------------------------------------------
print(f"\n{'='*55}")
print("  TERMINÉ")
print(f"{'='*55}")
print(f"  players_all_clean.csv -> {len(df):,} joueurs")
print(f"  players_maroc.csv     -> {len(df_maroc):,} joueurs marocains")
print(f"  config.json           -> scaler sauvegardé")
print(f"{'='*55}")

print(f"\nJoueurs marocains par poste :")
print(df_maroc["poste"].value_counts().to_string())

print(f"\n-> Étape suivante : python construction_graphe.py")


