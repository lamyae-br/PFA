"""
=============================================================
main.py — Backend FastAPI Multi-Nations PFA GNN
=============================================================
API REST qui sert :
  - La composition optimale pour TOUTES les nations
  - La liste des joueurs (mondial ou par nation)
  - Le vecteur PFA actuel
  - Les statistiques globales
  - La comparaison entre nations
  - Le top 3 par poste (mondial ou par nation)
=============================================================
Lancer  : cd backend && python -m uvicorn main:app --reload --port 8000
URL     : http://localhost:8000
Docs    : http://localhost:8000/docs
=============================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import composition, players, pfa, stats, nations, auth, compare, graph, editor
from data_loader import load_all_data

# ─────────────────────────────────────────────
# INITIALISATION
# ─────────────────────────────────────────────
print("=" * 55)
print("  DÉMARRAGE DU BACKEND PFA GNN — MULTI NATIONS")
print("=" * 55)

# Chargement unique des données au démarrage
load_all_data()

app = FastAPI(
    title="API Sélection Multi-Nations - GNN",
    description=(
        "Sélection optimale de la composition d'équipe via Graph Neural Networks. "
        "Supporte toutes les nationalités et plusieurs formations tactiques."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Autoriser le frontend React à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# ENREGISTREMENT DES ROUTES
# ─────────────────────────────────────────────
app.include_router(auth.router,        prefix="/api", tags=["Authentification"])
app.include_router(compare.router,     prefix="/api", tags=["Comparaison"])
app.include_router(composition.router, prefix="/api", tags=["Composition"])
app.include_router(players.router,     prefix="/api", tags=["Joueurs"])
app.include_router(pfa.router,         prefix="/api", tags=["Vecteur PFA"])
app.include_router(stats.router,       prefix="/api", tags=["Statistiques"])
app.include_router(nations.router,     prefix="/api", tags=["Nations"])
app.include_router(graph.router,       prefix="/api", tags=["Graphe"])
app.include_router(editor.router,      prefix="/api", tags=["Éditeur PFA"])

# ─────────────────────────────────────────────
# ROUTE RACINE
# ─────────────────────────────────────────────
@app.get("/", tags=["Accueil"])
def root():
    """Page d'accueil de l'API"""
    return {
        "message": "API Sélection Multi-Nations - GNN",
        "version": "2.0.0",
        "endpoints": {
            "composition_mondiale":  "/api/composition",
            "composition_par_nation": "/api/composition?nation=Morocco",
            "composition_formation": "/api/composition?formation=4-4-2&nation=Brazil",
            "liste_nations":         "/api/nations-list",
            "joueurs_par_nation":    "/api/players?nation=France",
            "joueur_par_nom":        "/api/players/{name}",
            "vecteur_pfa":           "/api/pfa-vector",
            "stats":                 "/api/stats",
            "comparaison_nations":   "/api/nations",
            "top_par_poste":         "/api/top-players",
            "documentation":         "/docs"
        },
        "formations_supportees": ["4-3-3", "4-4-2", "4-2-3-1", "3-5-2", "3-4-3", "5-3-2"]
    }

# ─────────────────────────────────────────────
# LANCEMENT DIRECT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)