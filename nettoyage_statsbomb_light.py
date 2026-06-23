"""
=============================================================
NETTOYAGE STATSBOMB — Version légère (anti-freeze PC)
=============================================================
Traitement fichier par fichier — ne charge jamais tout en RAM
=============================================================
"""

import os, json, warnings
import pandas as pd
import numpy as np
from glob import glob
from collections import defaultdict
from sklearn.preprocessing import MinMaxScaler
warnings.filterwarnings("ignore")

EVENTS_FOLDER = "events"
OUT_PLAYERS   = "players_statsbomb.csv"
OUT_INTERACT  = "interactions.csv"

# ─────────────────────────────────────────────
# LIMITE — pour ne pas bloquer le PC
# Mettez 50 pour tester, puis augmentez
# ─────────────────────────────────────────────
MAX_FILES =     100000 # ← changez cette valeur

print("=" * 55)
print("  NETTOYAGE STATSBOMB — VERSION LÉGÈRE")
print("=" * 55)

files = glob(os.path.join(EVENTS_FOLDER, "*.json"))
if not files:
    print(f"ERREUR : aucun fichier .json dans '{EVENTS_FOLDER}/'")
    exit()

files = files[:MAX_FILES]
print(f"Fichiers à traiter : {len(files)} (limite : {MAX_FILES})")

# ─────────────────────────────────────────────
# TRAITEMENT FICHIER PAR FICHIER
# Jamais tout en mémoire en même temps
# ─────────────────────────────────────────────
# Accumulateurs par joueur
player_stats  = defaultdict(lambda: {
    "goals": 0, "shots": 0, "xg": 0.0,
    "passes_total": 0, "passes_completed": 0,
    "pressings": 0, "duels": 0, "duels_won": 0,
    "carries": 0, "interceptions": 0,
})

# Accumulateur arêtes
edge_counter = defaultdict(int)

print("\nTraitement en cours...")
errors = 0

for i, file in enumerate(files):
    try:
        with open(file, encoding="utf-8") as f:
            events = json.load(f)

        for ev in events:
            # Récupérer le nom du joueur
            player = ev.get("player", {})
            if not player:
                continue
            name = player.get("name")
            if not name:
                continue

            ev_type = ev.get("type", {}).get("name", "")
            s = player_stats[name]

            # ── TIRS
            if ev_type == "Shot":
                s["shots"] += 1
                shot = ev.get("shot", {})
                outcome = shot.get("outcome", {}).get("name", "")
                if outcome == "Goal":
                    s["goals"] += 1
                s["xg"] += float(shot.get("statsbomb_xg", 0) or 0)

            # ── PASSES
            elif ev_type == "Pass":
                s["passes_total"] += 1
                pass_data = ev.get("pass", {})
                # Passe complète = pas d'outcome
                if "outcome" not in pass_data:
                    s["passes_completed"] += 1

                # Arête A → B
                recipient = pass_data.get("recipient", {})
                if recipient:
                    rec_name = recipient.get("name")
                    if rec_name and rec_name != name:
                        edge_counter[(name, rec_name)] += 1

            # ── PRESSING
            elif ev_type == "Pressure":
                s["pressings"] += 1

            # ── DUELS
            elif ev_type == "Duel":
                s["duels"] += 1
                duel_outcome = ev.get("duel", {}).get("outcome", {}).get("name", "")
                if duel_outcome in ["Won", "Success", "Success In Play", "Success Out"]:
                    s["duels_won"] += 1

            # ── CARRIES
            elif ev_type == "Carry":
                s["carries"] += 1

            # ── INTERCEPTIONS
            elif ev_type == "Interception":
                s["interceptions"] += 1

        # Afficher la progression
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(files)} fichiers traités | "
                  f"joueurs: {len(player_stats)} | "
                  f"arêtes: {len(edge_counter)}")

    except Exception as e:
        errors += 1
        print(f"  [!] Fichier ignoré : {os.path.basename(file)} → {e}")
        continue

print(f"\nTerminé : {len(files)-errors} fichiers OK | {errors} erreurs")

# ─────────────────────────────────────────────
# CONSTRUIRE LE DATAFRAME JOUEURS
# ─────────────────────────────────────────────
print("\nConstruction du dataset joueurs...")

rows = []
for name, s in player_stats.items():
    pass_acc   = round(s["passes_completed"] / s["passes_total"], 4) \
                 if s["passes_total"] > 0 else 0
    duel_rate  = round(s["duels_won"] / s["duels"], 4) \
                 if s["duels"] > 0 else 0
    goal_ratio = round(s["goals"] / s["xg"], 4) \
                 if s["xg"] > 0 else 0

    rows.append({
        "short_name"       : name,
        "goals"            : s["goals"],
        "shots"            : s["shots"],
        "xg_total"         : round(s["xg"], 4),
        "passes_total"     : s["passes_total"],
        "passes_completed" : s["passes_completed"],
        "pass_accuracy"    : pass_acc,
        "pressings"        : s["pressings"],
        "duels_total"      : s["duels"],
        "duels_won"        : s["duels_won"],
        "duel_win_rate"    : duel_rate,
        "carries"          : s["carries"],
        "interceptions"    : s["interceptions"],
        "goal_ratio"       : goal_ratio,
    })

df_players = pd.DataFrame(rows)
print(f"Joueurs extraits : {len(df_players)}")

# ─────────────────────────────────────────────
# NORMALISATION [0, 1]
# ─────────────────────────────────────────────
NORM_COLS = [
    "goals", "shots", "xg_total",
    "passes_total", "passes_completed", "pass_accuracy",
    "pressings", "duels_total", "duel_win_rate",
    "carries", "interceptions", "goal_ratio",
]
NORM_COLS = [c for c in NORM_COLS if c in df_players.columns]

scaler = MinMaxScaler()
df_players[NORM_COLS] = scaler.fit_transform(df_players[NORM_COLS])

# ─────────────────────────────────────────────
# CONSTRUIRE LES ARÊTES
# ─────────────────────────────────────────────
print("\nConstruction des arêtes...")

edges = [
    {"joueur_a": a, "joueur_b": b, "nb_passes": cnt}
    for (a, b), cnt in edge_counter.items()
]
df_edges = pd.DataFrame(edges)

if len(df_edges) > 0:
    df_edges["poids"] = (
        df_edges["nb_passes"] / df_edges["nb_passes"].max()
    ).round(4)
    # Garder seulement arêtes significatives (min 2 passes)
    df_edges = df_edges[df_edges["nb_passes"] >= 2].reset_index(drop=True)

print(f"Arêtes extraites : {len(df_edges):,}")

# ─────────────────────────────────────────────
# SAUVEGARDE
# ─────────────────────────────────────────────
df_players.to_csv(OUT_PLAYERS, index=False)
df_edges.to_csv(OUT_INTERACT, index=False)

print(f"\n{'='*55}")
print("  TERMINÉ")
print(f"{'='*55}")
print(f"  players_statsbomb.csv → {len(df_players)} joueurs")
print(f"  interactions.csv      → {len(df_edges):,} arêtes")
print(f"{'='*55}")
print(f"\nSi le PC était lent → réduisez MAX_FILES = 20")
print(f"Si tout va bien     → augmentez MAX_FILES = 200")
