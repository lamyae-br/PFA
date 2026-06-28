"""
plot_coherence.py
Compare la composition generee par le systeme vs la selection officielle marocaine.
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patches as mpatches

mpl.rcParams.update({'font.family': 'serif', 'font.size': 10})

# Composition generee par le systeme
systeme = {
    "GKP": [("Y. Bounou", 0.7966)],
    "DEF": [("A. Hakimi", 0.7734), ("N. Mazraoui", 0.7545),
            ("N. Aguerd", 0.7369), ("R. Saiss", 0.7249)],
    "MIL": [("S. Amrabat", 0.7149), ("A. Harit", 0.7136), ("A. Taarabt", 0.7065)],
    "ATT": [("H. Ziyech", 0.7564), ("Munir", 0.7179), ("Y. En-Nesyri", 0.7171)],
}

# Selection officielle reelle (Walid Regragui, 2022-2023)
officielle = {
    "GKP": ["Y. Bounou"],
    "DEF": ["A. Hakimi", "N. Mazraoui", "N. Aguerd", "R. Saiss"],
    "MIL": ["S. Amrabat", "A. Ounahi", "A. Harit"],
    "ATT": ["H. Ziyech", "Y. En-Nesyri", "S. Boufal"],
}

POSTES   = ["GKP", "DEF", "MIL", "ATT"]
LABELS   = {"GKP": "Gardien", "DEF": "Defenseurs", "MIL": "Milieux", "ATT": "Attaquants"}
COLOR_OK  = "#16a34a"   # vert  — joueur en commun
COLOR_NO  = "#c8102e"   # rouge — joueur different
COLOR_HDR = "#1e3a5f"   # bleu fonce — entete poste

fig, (ax_left, ax_right) = plt.subplots(1, 2, figsize=(13, 7))

for ax in (ax_left, ax_right):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

def draw_column(ax, title, postes_data, postes_ref, is_system=True):
    ax.text(0.5, 0.97, title, ha="center", va="top", fontsize=13,
            fontweight="bold", color=COLOR_HDR)
    ax.axhline(y=0.93, color=COLOR_HDR, linewidth=1.5, xmin=0.05, xmax=0.95)

    y = 0.88
    for poste in POSTES:
        # Entete poste
        ax.text(0.5, y, LABELS[poste], ha="center", va="center",
                fontsize=9, fontweight="bold", color="white",
                bbox=dict(boxstyle="round,pad=0.3", facecolor=COLOR_HDR,
                          edgecolor="none", alpha=0.85))
        y -= 0.055

        if is_system:
            joueurs = postes_data.get(poste, [])
            ref_noms = postes_ref.get(poste, [])
            for nom, score in joueurs:
                en_commun = nom in ref_noms
                color = COLOR_OK if en_commun else COLOR_NO
                marker = "[OK]" if en_commun else "[--]"
                line = f"{marker}  {nom}  ({score:.4f})"
                ax.text(0.5, y, line, ha="center", va="center",
                        fontsize=9.5, color=color, fontweight="bold")
                y -= 0.048
        else:
            joueurs = postes_data.get(poste, [])
            ref_sys = [n for n, _ in postes_ref.get(poste, [])]
            for nom in joueurs:
                en_commun = nom in ref_sys
                color = COLOR_OK if en_commun else "#92400e"
                marker = "[OK]" if en_commun else "[--]"
                line = f"{marker}  {nom}"
                ax.text(0.5, y, line, ha="center", va="center",
                        fontsize=9.5, color=color, fontweight="bold")
                y -= 0.048
        y -= 0.01

draw_column(ax_left,  "Systeme GNN", systeme,    officielle, is_system=True)
draw_column(ax_right, "Selection officielle",
            officielle, systeme,    is_system=False)

# Legende
patch_ok = mpatches.Patch(color=COLOR_OK, label="Joueur en commun")
patch_no = mpatches.Patch(color=COLOR_NO, label="Propose uniquement par le systeme")
patch_of = mpatches.Patch(color="#92400e", label="Selectionne uniquement officiellement")
fig.legend(handles=[patch_ok, patch_no, patch_of],
           loc="lower center", ncol=3, fontsize=9,
           bbox_to_anchor=(0.5, 0.01), framealpha=0.9)

fig.suptitle("Coherence entre la composition generee et la selection officielle marocaine",
             fontsize=12, fontweight="bold", y=1.01)

plt.tight_layout()
plt.savefig("coherence_selection.png", dpi=200, bbox_inches="tight")
plt.savefig("coherence_selection.pdf", bbox_inches="tight")
print("Sauvegarde : coherence_selection.png et coherence_selection.pdf")
plt.show()
