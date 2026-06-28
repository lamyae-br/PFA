"""
plot_holdout.py
Génère le scatter plot scores prédits vs scores réels pour les joueurs marocains.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({'font.family': 'serif', 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False})

df = pd.read_csv("resultats_jamais_vus.csv", encoding="utf-8")

if "pfa_true" not in df.columns or "score_holdout" not in df.columns:
    print("Colonnes manquantes dans resultats_jamais_vus.csv")
    exit()

y_true = df["pfa_true"].values
y_pred = df["score_holdout"].values

fig, ax = plt.subplots(figsize=(7, 6))

ax.scatter(y_true, y_pred, color='#c8102e', alpha=0.7, edgecolors='white',
           linewidths=0.5, s=60, zorder=3)

lims = [min(y_true.min(), y_pred.min()) - 0.02,
        max(y_true.max(), y_pred.max()) + 0.02]
ax.plot(lims, lims, 'k--', linewidth=1.2, alpha=0.5, label='Prediction parfaite')

mae = np.mean(np.abs(y_true - y_pred))
r2  = 1 - np.sum((y_true - y_pred)**2) / np.sum((y_true - y_true.mean())**2)

ax.set_xlabel('Score PFA reel (similarite cosinus)', fontsize=11)
ax.set_ylabel('Score PFA predit (modele holdout)', fontsize=11)
ax.set_title('Modele holdout : scores predits vs reels\n(121 joueurs marocains jamais vus)',
             fontsize=12, fontweight='bold', pad=12)
ax.legend(fontsize=10)
ax.text(0.05, 0.92, f'MAE = {mae:.4f}\nR2  = {r2:.4f}',
        transform=ax.transAxes, fontsize=10,
        bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#c8102e', alpha=0.8))
ax.grid(True, alpha=0.25, linestyle='--')

plt.tight_layout()
plt.savefig('holdout_scatter.png', dpi=200, bbox_inches='tight')
plt.savefig('holdout_scatter.pdf', bbox_inches='tight')
print("Sauvegarde : holdout_scatter.png et holdout_scatter.pdf")
plt.show()
