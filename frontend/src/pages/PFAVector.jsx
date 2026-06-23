import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { getPfaVector } from '../services/api'
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts'
import { Loader } from 'lucide-react'

export default function PFAVector() {
  const [pfa, setPfa] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getPfaVector()
      .then(setPfa)
      .catch(() => setError('Impossible de charger le vecteur PFA. Vérifiez que le backend est démarré.'))
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

  if (!pfa) {
    return (
      <div className="flex justify-center py-24">
        <Loader className="w-8 h-8 animate-spin text-accent" />
      </div>
    )
  }

  const data = Object.entries(pfa.vector).map(([key, value]) => ({
    feature: key.replace(/_/g, ' ').replace('goalkeeping ', 'gk_'),
    value: parseFloat(value)
  }))

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">
      <div className="mb-12">
        <div className="font-mono text-xs tracking-widest uppercase text-accent mb-4">
          / Vecteur PFA
        </div>
        <h1 className="font-display text-5xl md:text-7xl tracking-tight">
          Profil <span className="text-accent">tactique</span>
        </h1>
        <p className="mt-6 text-ink/70 max-w-2xl">
          {pfa.description}
        </p>
        <div className="mt-4 font-mono text-xs text-ink/50">
          {pfa.dimensions} dimensions
        </div>
      </div>

      <div className="grid lg:grid-cols-5 gap-8">
        {/* RADAR */}
        <div className="lg:col-span-3 bg-white border border-ink/10 p-6">
          <div className="font-mono text-[10px] tracking-widest uppercase text-ink/60 mb-4">
            / Radar chart
          </div>
          <ResponsiveContainer width="100%" height={500}>
            <RadarChart data={data}>
              <PolarGrid stroke="#0a0a0a20" />
              <PolarAngleAxis dataKey="feature" tick={{ fontSize: 10, fill: '#0a0a0a' }} />
              <PolarRadiusAxis angle={90} domain={[0, 1]} tick={{ fontSize: 9 }} />
              <Radar
                name="PFA"
                dataKey="value"
                stroke="#c8102e"
                fill="#c8102e"
                fillOpacity={0.3}
                strokeWidth={2}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* VALEURS */}
        <div className="lg:col-span-2 space-y-1">
          <div className="font-mono text-[10px] tracking-widest uppercase text-ink/60 mb-3">
            / Valeurs
          </div>
          {[...data].sort((a, b) => b.value - a.value).map((d, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.03 }}
              className="bg-white border border-ink/10 p-3"
            >
              <div className="flex justify-between items-center text-xs">
                <span className="font-mono uppercase tracking-wide truncate">{d.feature}</span>
                <span className="font-display text-lg text-accent ml-3">{d.value.toFixed(2)}</span>
              </div>
              <div className="mt-2 h-1 bg-ink/10 rounded-full overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${d.value * 100}%` }}
                  transition={{ delay: i * 0.03, duration: 0.7 }}
                  className="h-full bg-accent"
                />
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}
