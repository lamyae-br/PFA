"""
plot_nations_audit.py
Génère le graphique des scores PFA totaux par nation pour le rapport.
"""
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np

mpl.rcParams.update({'font.family': 'serif', 'font.size': 11,
                     'axes.spines.top': False, 'axes.spines.right': False})

nations = ['France', 'Bresil', 'Argentine', 'Espagne', 'Maroc',
           'Portugal', 'Angleterre', 'Allemagne', 'Senegal']
scores  = [8.42, 8.31, 8.28, 8.19, 8.14, 8.15, 8.07, 7.98, 7.87]
colors  = ['#9ca3af'] * len(nations)
colors[nations.index('Maroc')] = '#c8102e'

idx = np.argsort(scores)[::-1]
nations_sorted = [nations[i] for i in idx]
scores_sorted  = [scores[i]  for i in idx]
colors_sorted  = [colors[i]  for i in idx]

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.barh(nations_sorted, scores_sorted,
               color=colors_sorted, edgecolor='white', height=0.6)

for bar, val, nation in zip(bars, scores_sorted, nations_sorted):
    color = '#c8102e' if nation == 'Maroc' else '#374151'
    ax.text(val + 0.01, bar.get_y() + bar.get_height()/2,
            f'{val:.2f}', va='center', fontsize=10,
            color=color,
            fontweight='bold' if nation == 'Maroc' else 'normal')

ax.set_xlabel('Score PFA total (somme des 11 joueurs)', fontsize=11)
ax.set_title('Score PFA total par nation -- Formation 4-3-3',
             fontsize=12, fontweight='bold', pad=12)
ax.set_xlim(7.7, 8.6)
ax.invert_yaxis()
ax.grid(True, alpha=0.25, linestyle='--', axis='x')

plt.tight_layout()
plt.savefig('audit_nations.png', dpi=200, bbox_inches='tight')
plt.savefig('audit_nations.pdf', bbox_inches='tight')
print("Sauvegarde : audit_nations.png et audit_nations.pdf")
plt.show()
