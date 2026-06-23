import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { getPlayers, getNationsList } from '../services/api'
import { Search, Loader, ChevronDown } from 'lucide-react'

const POSTES = ['', 'GKP', 'DEF', 'MIL', 'ATT']

export default function Players() {
  const [players, setPlayers] = useState([])
  const [nations, setNations] = useState([])
  const [nation, setNation] = useState('')
  const [poste, setPoste] = useState('')
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    getNationsList(11)
      .then(d => setNations(d.nations || []))
      .catch(() => setError('Impossible de charger la liste des nations.'))
  }, [])

  useEffect(() => {
    setLoading(true)
    setError(null)
    getPlayers({
      nation: nation || undefined,
      poste: poste || undefined,
      limit: 100
    })
      .then(data => { setPlayers(data); setError(null) })
      .catch(e => {
        setPlayers([])
        setError(e?.response?.data?.detail || 'Erreur lors du chargement des joueurs.')
      })
      .finally(() => setLoading(false))
  }, [nation, poste])

  const filtered = search
    ? players.filter(p => p.short_name.toLowerCase().includes(search.toLowerCase()))
    : players

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">

      <div className="mb-12">
        <div className="font-mono text-xs tracking-widest uppercase text-accent mb-4">
          / Explorateur de joueurs
        </div>
        <h1 className="font-display text-5xl md:text-7xl tracking-tight">
          Tous les <span className="text-accent">joueurs</span>
        </h1>
        <p className="mt-6 text-ink/70 max-w-2xl">
          Explorez les scores PFA de tous les joueurs du dataset.
          Filtrez par nation, poste ou nom.
        </p>
      </div>

      {/* Filtres */}
      <div className="grid md:grid-cols-3 gap-4 mb-8">
        <SelectField
          label="Nation"
          value={nation}
          onChange={setNation}
          options={[
            { value: '', label: 'Toutes nations' },
            ...nations.map(n => ({ value: n.nation, label: n.nation }))
          ]}
        />
        <SelectField
          label="Poste"
          value={poste}
          onChange={setPoste}
          options={POSTES.map(p => ({ value: p, label: p || 'Tous postes' }))}
        />
        <SearchField value={search} onChange={setSearch} />
      </div>

      {/* Liste */}
      {error && (
        <div className="border-2 border-accent p-6 bg-accent/5 mb-6">
          <div className="font-mono text-xs uppercase tracking-widest text-accent mb-1">Erreur</div>
          <div className="text-ink/80 text-sm">{error}</div>
        </div>
      )}
      {loading ? (
        <div className="flex justify-center py-24">
          <Loader className="w-8 h-8 animate-spin text-accent" />
        </div>
      ) : (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filtered.map((p, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: Math.min(i * 0.02, 0.5) }}
              className="bg-white border border-ink/10 p-4 hover:border-accent hover:shadow-md transition-all group"
            >
              <div className="flex justify-between items-start mb-3">
                <div className="font-medium">{p.short_name}</div>
                <span className="bg-ink text-cream text-[10px] px-2 py-0.5 rounded-sm">
                  {p.poste}
                </span>
              </div>
              <div className="text-xs text-ink/60 mb-3 truncate">{p.club}</div>
              <div className="flex items-end justify-between border-t border-ink/10 pt-3">
                <div>
                  <div className="text-[9px] uppercase tracking-widest text-ink/50">Overall</div>
                  <div className="font-display text-2xl">{p.overall}</div>
                </div>
                <div className="text-right">
                  <div className="text-[9px] uppercase tracking-widest text-ink/50">PFA</div>
                  <div className="font-display text-2xl text-accent">{p.pfa_score}</div>
                </div>
              </div>
              <div className="mt-3 text-[10px] font-mono text-ink/50 truncate">
                {p.nationality}
              </div>
            </motion.div>
          ))}
          {filtered.length === 0 && !loading && (
            <div className="col-span-full text-center py-16 text-ink/40">
              Aucun joueur trouvé.
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function SelectField({ label, value, onChange, options }) {
  return (
    <label className="block">
      <span className="text-[10px] uppercase tracking-widest text-ink/60 font-medium">{label}</span>
      <div className="relative mt-2">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-white border border-ink/20 px-4 py-3 appearance-none focus:border-accent focus:outline-none"
        >
          {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink/40 pointer-events-none" />
      </div>
    </label>
  )
}

function SearchField({ value, onChange }) {
  return (
    <label className="block">
      <span className="text-[10px] uppercase tracking-widest text-ink/60 font-medium">Recherche</span>
      <div className="relative mt-2">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink/40" />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder="Nom du joueur..."
          className="w-full bg-white border border-ink/20 pl-10 pr-4 py-3 focus:border-accent focus:outline-none"
        />
      </div>
    </label>
  )
}
