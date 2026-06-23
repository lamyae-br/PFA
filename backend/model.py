"""
=============================================================
model.py — Architecture du Graph Neural Network
=============================================================
GraphSAGE 3 couches + BatchNorm — identique à l'entraînement.
=============================================================
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import SAGEConv


class GNN(nn.Module):
    """GraphSAGE 3 couches + BatchNorm + tête de régression."""

    def __init__(self, in_dim, hidden, out_dim):
        super().__init__()
        self.conv1 = SAGEConv(in_dim, hidden)
        self.bn1   = nn.BatchNorm1d(hidden)
        self.conv2 = SAGEConv(hidden, hidden)
        self.bn2   = nn.BatchNorm1d(hidden)
        self.conv3 = SAGEConv(hidden, out_dim)
        self.bn3   = nn.BatchNorm1d(out_dim)
        self.head = nn.Sequential(
            nn.Linear(out_dim, 32),
            nn.ReLU(),
            nn.Dropout(0.0),
            nn.Linear(32, 1),
            nn.Sigmoid(),
        )

    def encode(self, x, edge_index):
        x = self.bn1(F.relu(self.conv1(x, edge_index)))
        x = self.bn2(F.relu(self.conv2(x, edge_index)))
        return self.bn3(self.conv3(x, edge_index))

    def forward(self, x, edge_index):
        emb = self.encode(x, edge_index)
        return emb, self.head(emb).squeeze(-1)
