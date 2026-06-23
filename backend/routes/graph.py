"""
routes/graph.py — Sous-graphe GNN des 11 joueurs sélectionnés
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import Optional, List
from pydantic import BaseModel
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity as cosine_sim

from data_loader import get_data, get_players, get_exclusions
from dependencies import get_current_user

router = APIRouter()

FORMATIONS = {
    "4-3-3":   {"GKP": 1, "DEF": 4, "MIL": 3, "ATT": 3},
    "4-4-2":   {"GKP": 1, "DEF": 4, "MIL": 4, "ATT": 2},
    "4-2-3-1": {"GKP": 1, "DEF": 4, "MIL": 5, "ATT": 1},
    "3-5-2":   {"GKP": 1, "DEF": 3, "MIL": 5, "ATT": 2},
    "3-4-3":   {"GKP": 1, "DEF": 3, "MIL": 4, "ATT": 3},
    "5-3-2":   {"GKP": 1, "DEF": 5, "MIL": 3, "ATT": 2},
}

SIM_THRESHOLD = 0.85  # seuil pour les arêtes de similarité


# ─────────────────────────────────────────────
# Schémas de réponse
# ─────────────────────────────────────────────

class GraphNode(BaseModel):
    id:          str
    name:        str
    poste:       str
    club:        str
    nationality: str
    overall:     int
    pfa_score:   float


class GraphEdge(BaseModel):
    source: str
    target: str
    weight: float
    type:   str   # "graphe" | "similarite"


class GraphStats(BaseModel):
    total_nodes:      int
    total_edges:      int
    graphe_edges:     int
    similarite_edges: int


class GraphResponse(BaseModel):
    nodes:     List[GraphNode]
    edges:     List[GraphEdge]
    formation: str
    nation:    str
    stats:     GraphStats


# ─────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────

@router.get("/graph", response_model=GraphResponse)
def get_graph(
    formation: str = Query("4-3-3"),
    nation: Optional[str] = Query(None),
    _user: dict = Depends(get_current_user),
):
    """
    Retourne le sous-graphe GNN des 11 joueurs de la composition optimale.
    Les arêtes proviennent soit du graphe (graph_data.pt) soit d'une similarité cosinus > seuil.
    """
    df_all = get_players()
    graph_data = get_data()
    EXCLUSIONS = get_exclusions()

    if formation not in FORMATIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Formation '{formation}' non supportée. Choisir parmi : {list(FORMATIONS.keys())}"
        )

    # ── 1. Sélectionner les 11 joueurs (même logique que /composition) ──
    if nation:
        if "nationality_name" not in df_all.columns:
            raise HTTPException(status_code=400, detail="Colonne nationality_name manquante")
        df = df_all[df_all["nationality_name"] == nation].copy()
        if len(df) == 0:
            raise HTTPException(status_code=404, detail=f"Nation '{nation}' introuvable")
    else:
        df = df_all.copy()

    if nation == "Morocco":
        df = df[~df["short_name"].str.lower().isin(EXCLUSIONS)]

    players_11 = []
    FORMATION = FORMATIONS[formation]
    for poste, nb in FORMATION.items():
        top = df[df["poste"] == poste].nlargest(nb, "pfa_score")
        if len(top) < nb:
            raise HTTPException(
                status_code=400,
                detail=f"Pas assez de joueurs au poste {poste} pour '{nation or 'mondial'}'. "
                       f"Trouvé {len(top)}/{nb}."
            )
        players_11.extend(top.to_dict("records"))

    # ── 2. Construire le mapping nom → player_id ──
    name_to_id = {}
    id_to_row  = {}
    for row in players_11:
        pid = int(row["player_id"])
        name = str(row["short_name"])
        name_to_id[name] = pid
        id_to_row[pid]   = row

    all_ids = list(name_to_id.values())
    idx_set = set(all_ids)

    # ── 3. Extraire les arêtes du graphe (vectorisé) ──
    edges_np   = graph_data.edge_index.numpy().T   # (E, 2)
    has_attr   = graph_data.edge_attr is not None and graph_data.edge_attr.numel() > 0
    weights_np = graph_data.edge_attr.numpy().flatten() if has_attr else np.ones(len(edges_np))

    idx_array = np.array(all_ids)
    mask = np.isin(edges_np[:, 0], idx_array) & np.isin(edges_np[:, 1], idx_array)
    sub_edges   = edges_np[mask]
    sub_weights = weights_np[mask]

    # Dédupliquer les arêtes bidirectionnelles
    if len(sub_edges) > 0:
        dedup_mask  = sub_edges[:, 0] < sub_edges[:, 1]
        sub_edges   = sub_edges[dedup_mask]
        sub_weights = sub_weights[dedup_mask]

    # Convertir player_id → short_name
    id_to_name = {v: k for k, v in name_to_id.items()}
    graph_edge_pairs = set()
    graphe_edges = []

    for i, (src, dst) in enumerate(sub_edges):
        src_name = id_to_name.get(int(src))
        dst_name = id_to_name.get(int(dst))
        if src_name and dst_name:
            graphe_edges.append(GraphEdge(
                source=src_name,
                target=dst_name,
                weight=round(float(sub_weights[i]), 4),
                type="graphe",
            ))
            graph_edge_pairs.add((src_name, dst_name))

    # ── 4. Arêtes de similarité cosinus pour les paires non connectées ──
    X_11 = graph_data.x.numpy()[all_ids]   # (11, features)
    sim_matrix = cosine_sim(X_11)           # (11, 11)

    similarite_edges = []
    for i in range(len(all_ids)):
        for j in range(i + 1, len(all_ids)):
            name_i = id_to_name[all_ids[i]]
            name_j = id_to_name[all_ids[j]]
            pair = (name_i, name_j)
            pair_rev = (name_j, name_i)
            if pair not in graph_edge_pairs and pair_rev not in graph_edge_pairs:
                sim = float(sim_matrix[i, j])
                if sim >= SIM_THRESHOLD:
                    similarite_edges.append(GraphEdge(
                        source=name_i,
                        target=name_j,
                        weight=round(sim, 4),
                        type="similarite",
                    ))

    all_edges = graphe_edges + similarite_edges

    # ── 5. Construire les nœuds ──
    nodes = [
        GraphNode(
            id=str(row["short_name"]),
            name=str(row["short_name"]),
            poste=str(row["poste"]),
            club=str(row.get("club_name", "?")),
            nationality=str(row.get("nationality_name", nation or "World")),
            overall=int(row.get("overall_raw", 0)),
            pfa_score=round(float(row.get("pfa_score", 0)), 4),
        )
        for row in players_11
    ]

    return GraphResponse(
        nodes=nodes,
        edges=all_edges,
        formation=formation,
        nation=nation or "World",
        stats=GraphStats(
            total_nodes=len(nodes),
            total_edges=len(all_edges),
            graphe_edges=len(graphe_edges),
            similarite_edges=len(similarite_edges),
        ),
    )
