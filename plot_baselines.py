"""
plot_baselines.py
Génère le graphique de comparaison GNN vs baselines ML pour le rapport.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    'font.family':      'serif',
    'font.size':        11,
    'axes.spines.top':  False,
    'axes.spines.right':False,
    'axes.grid':        True,
    'grid.alpha':       0.3,
    'grid.linestyle':   '--',
})

models  = ['Moyenne\nnaïve', 'Ridge', 'Arbre de\ndécision',
           'GraphSAGE\n(GNN)', 'KNN\n(k=5)', 'Gradient\nBoosting']
mae     = [0.0192, 0.0053, 0.0035, 0.0035, 0.0016, 0.0013]
r2      = [-0.0003, 0.9317, 0.9647, 0.9715, 0.9886, 0.9953]
colors  = ['#9ca3af','#9ca3af','#9ca3af','#c8102e','#9ca3af','#9ca3af']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))

# ── Graphique MAE ─────────────────────────────────────────────
bars1 = ax1.barh(models, mae, color=colors, edgecolor='white', height=0.55)
ax1.set_xlabel('MAE (erreur absolue moyenne)', fontsize=11)
ax1.set_title('MAE — plus c\'est bas, mieux c\'est', fontsize=11, fontweight='bold')
ax1.invert_yaxis()
for bar, val in zip(bars1, mae):
    ax1.text(val + 0.001, bar.get_y() + bar.get_height()/2,
             f'{val:.4f}', va='center', fontsize=9,
             color='#c8102e' if val == min(mae) else '#374151',
             fontweight='bold' if val == min(mae) else 'normal')
ax1.set_xlim(0, max(mae) * 1.25)

# ── Graphique R² ──────────────────────────────────────────────
bars2 = ax2.barh(models, r2, color=colors, edgecolor='white', height=0.55)
ax2.set_xlabel('R² (coefficient de détermination)', fontsize=11)
ax2.set_title('R² — plus c\'est haut, mieux c\'est', fontsize=11, fontweight='bold')
ax2.invert_yaxis()
for bar, val in zip(bars2, r2):
    ax2.text(val + 0.005, bar.get_y() + bar.get_height()/2,
             f'{val:.4f}', va='center', fontsize=9,
             color='#c8102e' if val == max(r2) else '#374151',
             fontweight='bold' if val == max(r2) else 'normal')
ax2.set_xlim(0, 1.12)

fig.suptitle('Comparaison GraphSAGE vs baselines ML — Ensemble de validation',
             fontsize=13, fontweight='bold', y=1.02)

plt.tight_layout()
plt.savefig('baselines_comparison.png', dpi=200, bbox_inches='tight')
plt.savefig('baselines_comparison.pdf', bbox_inches='tight')
print("Graphique sauvegardé : baselines_comparison.png  et  baselines_comparison.pdf")
plt.show()
