"""
plot_routes.py
Genere une figure propre de l'organisation des routes backend.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib as mpl

mpl.rcParams.update({'font.family': 'monospace', 'font.size': 10})

fig, ax = plt.subplots(figsize=(10, 7))
ax.set_xlim(0, 10)
ax.set_ylim(0, 7)
ax.axis("off")

C_MAIN  = "#1e3a5f"
C_FILE  = "#c8102e"
C_ROUTE = "#15803d"
C_JSON  = "#92400e"

ax.text(5, 6.6, "Organisation modulaire du backend FastAPI",
        ha="center", va="center", fontsize=13,
        fontweight="bold", color=C_MAIN)

lines = [
    ("backend/",              0.3, 6.1, C_MAIN,  12, True),
    ("  main.py",             0.3, 5.65, C_FILE,  10, False),
    ("  auth.py",             0.3, 5.25, C_FILE,  10, False),
    ("  data_loader.py",      0.3, 4.85, C_FILE,  10, False),
    ("  dependencies.py",     0.3, 4.45, C_FILE,  10, False),
    ("  model.py",            0.3, 4.05, C_FILE,  10, False),
    ("  schemas.py",          0.3, 3.65, C_FILE,  10, False),
    ("  users.json",          0.3, 3.25, C_JSON,  10, False),
    ("  routes/",             0.3, 2.75, C_MAIN,  11, True),
    ("      auth.py",         0.3, 2.35, C_ROUTE, 10, False),
    ("      composition.py",  0.3, 1.95, C_ROUTE, 10, False),
    ("      players.py",      0.3, 1.55, C_ROUTE, 10, False),
    ("      compare.py",      0.3, 1.15, C_ROUTE, 10, False),
    ("      nations.py",      0.3, 0.75, C_ROUTE, 10, False),
    ("      stats.py",        0.3, 0.35, C_ROUTE, 10, False),
]

comments = {
    "  main.py":          "# Initialisation FastAPI + CORS + enregistrement routes",
    "  auth.py":          "# Logique JWT, bcrypt, lecture/ecriture users.json",
    "  data_loader.py":   "# Chargement unique modeles + calcul scores PFA",
    "  dependencies.py":  "# Verification token JWT (injection de dependance)",
    "  model.py":         "# Architecture GraphSAGE 3 couches",
    "  schemas.py":       "# Modeles Pydantic validation entrees/sorties",
    "  users.json":       "# Stockage comptes utilisateurs (pas de SQL)",
    "      auth.py":      "# POST /register  POST /login  GET /me",
    "      composition.py": "# GET /composition  /top-players  /nations-list",
    "      players.py":   "# GET /players  /players/{name}  /players/search",
    "      compare.py":   "# GET /compare  (radar chart 13 features)",
    "      nations.py":   "# GET /nations  /nations/africa",
    "      stats.py":     "# GET /stats  /evaluation",
}

for (label, x, y, color, fs, bold) in lines:
    ax.text(x, y, label, ha="left", va="center",
            fontsize=fs, color=color,
            fontweight="bold" if bold else "normal")
    if label in comments:
        ax.text(x + 3.2, y, comments[label],
                ha="left", va="center",
                fontsize=8.5, color="#6b7280", style="italic")

# Lignes de separateur
ax.axhline(y=2.95, xmin=0.03, xmax=0.97,
           color="#e5e7eb", linewidth=1, linestyle="--")

# Legende
p1 = mpatches.Patch(color=C_FILE,  label="Fichiers principaux")
p2 = mpatches.Patch(color=C_ROUTE, label="Modules de routes")
p3 = mpatches.Patch(color=C_JSON,  label="Stockage utilisateurs")
fig.legend(handles=[p1, p2, p3], loc="lower center", ncol=3,
           fontsize=9, bbox_to_anchor=(0.5, 0.01), framealpha=0.9)

plt.tight_layout()
plt.savefig("screen_swagger_routes.png", dpi=200, bbox_inches="tight")
plt.savefig("screen_swagger_routes.pdf", bbox_inches="tight")
print("Sauvegarde : screen_swagger_routes.png et screen_swagger_routes.pdf")
plt.show()
