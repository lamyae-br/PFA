"""
Tests des routes publiques — Stats et Nations
(sans charger PyTorch ni le graphe)
"""

import os
import sys
from unittest.mock import MagicMock, patch

# ── Mocker torch AVANT tout import du projet ──────────────────
# data_loader.py importe torch au niveau module ; on injecte un faux module
_torch_mock = MagicMock()
_torch_mock.load = MagicMock(return_value=MagicMock())
_torch_mock.no_grad = MagicMock(return_value=MagicMock(__enter__=MagicMock(return_value=None), __exit__=MagicMock(return_value=False)))
sys.modules.setdefault("torch", _torch_mock)
sys.modules.setdefault("torch.nn", MagicMock())
sys.modules.setdefault("torch.nn.functional", MagicMock())
sys.modules.setdefault("torch_geometric", MagicMock())
sys.modules.setdefault("torch_geometric.nn", MagicMock())
sys.modules.setdefault("torch_geometric.data", MagicMock())

import pytest
import pandas as pd
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ── Données mock ─────────────────────────────────────────────

MOCK_PLAYERS = pd.DataFrame({
    "player_id":        [0, 1, 2, 3],
    "short_name":       ["A. Hakimi", "Y. Bounou", "H. Ziyech", "R. Lewandowski"],
    "nationality_name": ["Morocco", "Morocco", "Morocco", "Poland"],
    "poste":            ["DEF", "GKP", "ATT", "ATT"],
    "overall":          [0.84, 0.82, 0.80, 0.91],
    "overall_raw":      [84, 82, 80, 91],
    "is_moroccan":      [1, 1, 1, 0],
    "club_name":        ["PSG", "Atletico", "Chelsea", "Bayern"],
    "pfa_score":        [0.74, 0.76, 0.70, 0.65],
    "pace":             [0.9, 0.5, 0.8, 0.7],
    "shooting":         [0.6, 0.2, 0.7, 0.9],
    "passing":          [0.8, 0.6, 0.85, 0.7],
    "dribbling":        [0.85, 0.4, 0.9, 0.6],
    "defending":        [0.75, 0.6, 0.5, 0.4],
    "physic":           [0.8, 0.7, 0.7, 0.85],
})

MOCK_DATA = MagicMock()
MOCK_DATA.x.shape = (4, 18)
MOCK_DATA.edge_index.shape = (2, 100)


@pytest.fixture(scope="module")
def client():
    with patch("data_loader.load_all_data"), \
         patch("data_loader.get_players", return_value=MOCK_PLAYERS), \
         patch("data_loader.get_data", return_value=MOCK_DATA):

        from main import app
        with TestClient(app) as c:
            yield c


# ── Tests route racine ────────────────────────────────────────

def test_root_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200


def test_root_contains_version(client):
    data = client.get("/").json()
    assert "version" in data
    assert data["version"] == "2.0.0"


def test_root_contains_endpoints(client):
    data = client.get("/").json()
    assert "endpoints" in data


# ── Tests route /api/stats ────────────────────────────────────

def test_stats_returns_200(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200


def test_stats_total_players(client):
    data = client.get("/api/stats").json()
    assert "total_players" in data
    assert data["total_players"] == 4


def test_stats_moroccan_players(client):
    data = client.get("/api/stats").json()
    assert "moroccan_players" in data
    assert data["moroccan_players"] == 3


def test_stats_has_gnn_metrics(client):
    data = client.get("/api/stats").json()
    assert "gnn_r2" in data
    assert "gnn_mae" in data


# ── Tests route /api/nations-list ────────────────────────────

def test_nations_list_returns_200(client):
    resp = client.get("/api/nations-list?min_players=1")
    assert resp.status_code == 200


def test_nations_list_structure(client):
    data = client.get("/api/nations-list?min_players=1").json()
    assert "total" in data
    assert "nations" in data
    assert isinstance(data["nations"], list)


# ── Tests route /api/evaluation ──────────────────────────────

def test_evaluation_returns_200(client):
    resp = client.get("/api/evaluation")
    assert resp.status_code == 200


def test_evaluation_has_methods(client):
    data = client.get("/api/evaluation").json()
    assert "methods" in data
    assert len(data["methods"]) > 0


# ── Tests authentification ────────────────────────────────────

def test_register_missing_fields(client):
    resp = client.post("/api/auth/register", json={})
    assert resp.status_code == 422


def test_login_wrong_credentials(client):
    resp = client.post("/api/auth/login", json={
        "email": "inconnu@example.com",
        "password": "mauvais"
    })
    assert resp.status_code == 401
