# Backend FastAPI Multi-Nations — Sélection Optimale GNN

API REST qui sert le modèle GNN pour la sélection optimale d'équipe **pour toutes les nationalités**.

## 📁 Structure

```
backend/
├── main.py              ← App FastAPI principale
├── model.py             ← Architecture GNN
├── data_loader.py       ← Chargement données + modèles
├── schemas.py           ← Validation Pydantic
├── requirements.txt     ← Dépendances
└── routes/
    ├── __init__.py
    ├── composition.py   ← Composition multi-nations
    ├── players.py       ← Joueurs (toutes nations)
    ├── pfa.py           ← Vecteur PFA
    ├── stats.py         ← Statistiques
    └── nations.py       ← Comparaison nations
```

## 🚀 Installation et lancement

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

**Documentation interactive** : http://localhost:8000/docs

## 🌍 Endpoints multi-nations

### Composition optimale

| URL | Description |
|---|---|
| `/api/composition` | **Meilleur XI mondial** |
| `/api/composition?nation=Morocco` | XI marocain |
| `/api/composition?nation=France` | XI français |
| `/api/composition?nation=Brazil` | XI brésilien |
| `/api/composition?nation=Argentina` | XI argentin |
| `/api/composition?nation=Spain&formation=4-4-2` | Espagne en 4-4-2 |

### Formations supportées

```
4-3-3     ← classique offensif
4-4-2     ← classique
4-2-3-1   ← moderne
3-5-2     ← italien
3-4-3     ← très offensif
5-3-2     ← défensif
```

### Autres endpoints

| URL | Description |
|---|---|
| `/api/nations-list` | Liste de toutes les nations disponibles |
| `/api/top-players?nation=Germany` | Top 3 allemands par poste |
| `/api/players?nation=Italy&poste=ATT` | Attaquants italiens |
| `/api/players/Hakimi` | Détails Hakimi |
| `/api/nations` | Top 20 nations par PFA |
| `/api/nations/africa` | Nations africaines |
| `/api/pfa-vector` | Vecteur PFA actuel |
| `/api/stats` | Stats globales |
| `/api/evaluation` | GNN vs baselines |

## 📊 Exemple — Composition du Brésil

`GET /api/composition?nation=Brazil&formation=4-3-3`

```json
{
  "formation": "4-3-3",
  "nation": "Brazil",
  "players": [
    {
      "short_name": "Alisson",
      "poste": "GKP",
      "club": "Liverpool",
      "overall": 89,
      "pfa_score": 0.7521,
      "nationality": "Brazil"
    },
    ...
  ],
  "total_pfa": 8.45
}
```

## 🔗 Frontend

Le frontend appelle l'API sur `http://localhost:8000/api/...`
CORS activé pour tous les domaines (à restreindre en production).
