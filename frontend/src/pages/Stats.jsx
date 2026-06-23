import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { getStats, getEvaluation, getNations } from '../services/api'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Loader, TrendingUp, Target, Activity } from 'lucide-react'

export default function Stats() {
  const [stats, setStats] = useState(null)
  const [eval_, setEval] = useState(null)
  const [nations, setNations] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      getStats(),
      getEvaluation(),
      getNations(10)
    ]).then(([s, e, n]) => {
      setStats(s)
      setEval(e)
      setNations(n)
    }).catch(() => setError('Impossible de charger les statistiques. Vérifiez que le backend est démarré.'))
  }, [])

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
        <div className="border-2 border-accent p-8 bg-accent/5">
          <div className="font-mono text-xs uppercase tracking-widest text-accent mb-2">Erreur</div>
          <div className="text-ink/80">{error}</div>
        </div>
      </div>
    )
  }

  if (!stats || !eval_) {
    return (
      <div className="flex justify-center py-24">
        <Loader className="w-8 h-8 animate-spin text-accent" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">

      <div className="mb-12">
        <div className="font-mono text-xs tracking-widest uppercase text-accent mb-4">
          / Statistiques · Performance
        </div>
        <h1 className="font-display text-5xl md:text-7xl tracking-tight">
          Le modèle, <span className="text-accent">en chiffres</span>
        </h1>
      </div>

      {/* KPIs */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-px bg-ink/10 mb-16">
        <Kpi label="R² du modèle" value={stats.gnn_r2.toFixed(4)} icon={<TrendingUp />} />
        <Kpi label="MAE" value={stats.gnn_mae.toFixed(4)} icon={<Target />} />
        <Kpi label="R² Holdout" value={stats.holdout_r2.toFixed(4)} icon={<Activity />} />
        <Kpi label="Joueurs" value={stats.total_players.toLocaleString()} icon={<Activity />} />
      </div>

      {/* Comparaison méthodes */}
      <section className="mb-16">
        <div className="font-mono text-[10px] tracking-widest uppercase text-ink/60 mb-3">
          / GNN vs Baselines ML
        </div>
        <div className="bg-white border border-ink/10 p-6">
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={eval_.methods}>
              <CartesianGrid strokeDasharray="3 3" stroke="#0a0a0a20" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} angle={-15} textAnchor="end" height={80} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip />
              <Bar dataKey="R2" name="R²">
                {eval_.methods.map((entry, i) => (
                  <Cell key={i} fill={entry.name.includes('GNN') ? '#c8102e' : '#0a0a0a80'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Top nations */}
      {nations && (
        <section className="mb-16">
          <div className="font-mono text-[10px] tracking-widest uppercase text-ink/60 mb-3">
            / Top 10 nations par score PFA moyen
          </div>
          <div className="bg-white border border-ink/10">
            <table className="w-full">
              <thead className="bg-ink text-cream">
                <tr>
                  <th className="text-left p-3 text-xs uppercase tracking-widest">#</th>
                  <th className="text-left p-3 text-xs uppercase tracking-widest">Nation</th>
                  <th className="text-right p-3 text-xs uppercase tracking-widest">Joueurs</th>
                  <th className="text-right p-3 text-xs uppercase tracking-widest">PFA moy</th>
                  <th className="text-right p-3 text-xs uppercase tracking-widest">PFA max</th>
                </tr>
              </thead>
              <tbody>
                {nations.nations.map((n, i) => (
                  <motion.tr
                    key={n.nation}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.04 }}
                    className="border-t border-ink/10 hover:bg-cream/50 transition-colors"
                  >
                    <td className="p-3 font-mono text-xs text-ink/60">{String(i+1).padStart(2,'0')}</td>
                    <td className="p-3 font-medium">{n.nation}</td>
                    <td className="p-3 text-right text-sm text-ink/70">{n.players_count}</td>
                    <td className="p-3 text-right font-mono text-sm">{n.pfa_avg}</td>
                    <td className="p-3 text-right font-mono text-sm text-accent">{n.pfa_max}</td>
                  </motion.tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Holdout */}
      <section className="bg-ink text-cream p-8 lg:p-12 mb-16">
        <div className="font-mono text-[10px] tracking-widest uppercase text-accent mb-3">
          / Test de généralisation (Holdout)
        </div>
        <h2 className="font-display text-4xl md:text-5xl mb-6">
          Le modèle <span className="text-accent">généralise.</span>
        </h2>
        <p className="text-cream/70 max-w-2xl mb-8">
          {eval_.holdout_test.description}. Sur les joueurs marocains jamais vus,
          le modèle atteint un R² de <strong className="text-accent">{eval_.holdout_test.moroccan_R2}</strong> —
          preuve qu'il a appris des patterns généraux et non une simple mémorisation.
        </p>
        <div className="grid sm:grid-cols-2 gap-px bg-cream/10">
          <div className="bg-ink p-6">
            <div className="font-display text-4xl text-accent">{eval_.holdout_test.moroccan_R2}</div>
            <div className="text-xs uppercase tracking-widest text-cream/60 mt-2">R² sur Marocains (jamais vus)</div>
          </div>
          <div className="bg-ink p-6">
            <div className="font-display text-4xl text-accent">{eval_.holdout_test.moroccan_MAE}</div>
            <div className="text-xs uppercase tracking-widest text-cream/60 mt-2">MAE sur Marocains</div>
          </div>
        </div>
      </section>
    </div>
  )
}

function Kpi({ label, value, icon }) {
  return (
    <div className="bg-cream p-6 hover:bg-white transition-colors">
      <div className="flex justify-between items-start mb-4">
        <div className="text-accent">{icon}</div>
        <div className="font-mono text-[10px] tracking-widest text-ink/40 uppercase">
          Modèle
        </div>
      </div>
      <div className="font-display text-4xl text-ink leading-none">{value}</div>
      <div className="text-[10px] uppercase tracking-widest text-ink/60 mt-2">{label}</div>
    </div>
  )
}
