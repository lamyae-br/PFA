"""
plot_architecture.py
Genere le schema d'architecture backend FastAPI + frontend React.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib as mpl

mpl.rcParams.update({'font.family': 'serif', 'font.size': 10})

fig, ax = plt.subplots(figsize=(13, 7))
ax.set_xlim(0, 13)
ax.set_ylim(0, 7)
ax.axis("off")

# ── Couleurs ──────────────────────────────────────────────────
C_FRONT  = "#1e40af"   # bleu  - frontend
C_BACK   = "#c8102e"   # rouge - backend
C_DATA   = "#15803d"   # vert  - donnees
C_USER   = "#6b21a8"   # violet - utilisateur
C_ARROW  = "#374151"
C_BOX    = "#f8fafc"

def box(ax, x, y, w, h, color, label, sublabel="", fontsize=10):
    rect = mpatches.FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.15", linewidth=2,
        edgecolor=color, facecolor=C_BOX)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2 + (0.18 if sublabel else 0),
            label, ha="center", va="center",
            fontsize=fontsize, fontweight="bold", color=color)
    if sublabel:
        ax.text(x + w/2, y + h/2 - 0.22, sublabel,
                ha="center", va="center", fontsize=8, color="#6b7280")

def header(ax, x, y, w, h, color, label):
    rect = mpatches.FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.1", linewidth=0,
        edgecolor=color, facecolor=color)
    ax.add_patch(rect)
    ax.text(x + w/2, y + h/2, label,
            ha="center", va="center",
            fontsize=11, fontweight="bold", color="white")

def arrow(ax, x1, y1, x2, y2, label="", color=C_ARROW):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=1.8))
    if label:
        mx, my = (x1+x2)/2, (y1+y2)/2
        ax.text(mx, my + 0.15, label, ha="center", va="bottom",
                fontsize=8, color=color,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white",
                          edgecolor=color, alpha=0.9))

# ── UTILISATEUR ───────────────────────────────────────────────
box(ax, 0.3, 2.8, 1.8, 1.4, C_USER, "Utilisateur", "Navigateur web")

# ── BLOC FRONTEND ─────────────────────────────────────────────
header(ax, 2.8, 5.6, 4.2, 0.55, C_FRONT, "FRONTEND  React 18 + Vite")

pages = [
    ("Accueil", 2.85, 4.7),
    ("Composition", 3.75, 4.7),
    ("Joueurs", 4.65, 4.7),
    ("Comparer", 5.55, 4.7),
    ("Graphe", 6.45, 4.7),  # shifted
]
for name, px, py in pages:
    box(ax, px, py, 0.82, 0.55, C_FRONT, name, fontsize=8)

# Tailwind / Recharts
ax.text(4.9, 4.25, "Tailwind CSS  |  Recharts  |  Framer Motion  |  Axios",
        ha="center", va="center", fontsize=8, color="#6b7280",
        style="italic")

# Contour frontend
rect_front = mpatches.FancyBboxPatch((2.8, 4.15), 4.2, 2.0,
    boxstyle="round,pad=0.1", linewidth=2,
    edgecolor=C_FRONT, facecolor="#eff6ff", alpha=0.35, zorder=0)
ax.add_patch(rect_front)

# ── COMMUNICATION ─────────────────────────────────────────────
# user -> frontend
arrow(ax, 2.1, 3.5, 2.8, 4.7, "HTTP", C_USER)

# frontend -> backend (requete)
arrow(ax, 7.0, 4.9, 8.2, 4.9, "Requete HTTP + JWT", C_FRONT)
# backend -> frontend (reponse)
arrow(ax, 8.2, 4.5, 7.0, 4.5, "JSON", C_BACK)

# ── BLOC BACKEND ──────────────────────────────────────────────
header(ax, 8.2, 5.6, 4.5, 0.55, C_BACK, "BACKEND  FastAPI  (Python)")

routes = [
    "/composition", "/players", "/compare",
    "/nations", "/stats", "/graph",
    "/pfa-vector", "/auth", "/editor",
]
cols = 3
for i, r in enumerate(routes):
    col = i % cols
    row = i // cols
    rx = 8.25 + col * 1.47
    ry = 4.7 - row * 0.65
    box(ax, rx, ry, 1.4, 0.52, C_BACK, r, fontsize=7.5)

# data_loader
ax.text(10.45, 3.1, "data_loader.py", ha="center", va="center",
        fontsize=9, fontweight="bold", color=C_BACK,
        bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff1f2",
                  edgecolor=C_BACK, linewidth=1.5))

# Contour backend
rect_back = mpatches.FancyBboxPatch((8.2, 2.9), 4.5, 2.75,
    boxstyle="round,pad=0.1", linewidth=2,
    edgecolor=C_BACK, facecolor="#fff1f2", alpha=0.35, zorder=0)
ax.add_patch(rect_back)

# ── BLOC DONNEES ──────────────────────────────────────────────
header(ax, 8.5, 1.3, 3.9, 0.45, C_DATA, "Donnees & Modeles")

data_items = [
    ("graph_data.pt", 8.55, 0.55),
    ("gnn_model.pt",  9.85, 0.55),
    ("players_final.csv", 11.1, 0.55),
]
for name, dx, dy in data_items:
    box(ax, dx, dy, 1.15, 0.52, C_DATA, name, fontsize=7.5)

# backend -> donnees
arrow(ax, 10.45, 2.9, 10.45, 1.75, "", C_DATA)

# Contour donnees
rect_data = mpatches.FancyBboxPatch((8.5, 0.4), 3.9, 1.35,
    boxstyle="round,pad=0.1", linewidth=2,
    edgecolor=C_DATA, facecolor="#f0fdf4", alpha=0.4, zorder=0)
ax.add_patch(rect_data)

# ── TITRE ─────────────────────────────────────────────────────
ax.text(6.5, 6.6, "Architecture de l'application web PFA-GNN",
        ha="center", va="center", fontsize=13,
        fontweight="bold", color="#111827")

ax.text(6.5, 6.2, "Client-Serveur  |  REST API  |  JWT  |  GraphSAGE",
        ha="center", va="center", fontsize=9,
        color="#6b7280", style="italic")

plt.tight_layout()
plt.savefig("architecture.png", dpi=200, bbox_inches="tight")
plt.savefig("architecture.pdf", bbox_inches="tight")
print("Sauvegarde : architecture.png et architecture.pdf")
plt.show()
