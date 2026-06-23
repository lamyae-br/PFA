import pandas as pd

# Tous les joueurs FIFA
all_players = pd.read_csv("dataset_gnn/players_all_clean.csv")
print("=== players_all_clean ===")
print(all_players.columns.tolist())
print(all_players.shape)

# Joueurs marocains
maroc = pd.read_csv("dataset_gnn/players_maroc.csv")
print("\n=== players_maroc ===")
print(maroc.columns.tolist())
print(maroc.shape)
print(maroc.head())