import { useEffect, useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, ResponsiveContainer,
} from 'recharts'
import { getEditorDefaultVector, postEditorComposition, getNationsList } from '../services/api'
import { Loader, RotateCcw, ChevronDown, ChevronUp } from 'lucide-react'

// ─────────────────────────────────────────────
// CONSTANTES
// ─────────────────────────────────────────────

const FORMATIONS = ['4-3-3', '4-4-2', '4-2-3-1', '3-5-2', '3-4-3', '5-3-2']

const LABELS = {
  pace:                    'Vitesse',
  physic:                  'Physique',
  power_stamina:           'Endurance',
  shooting:                'Tir',
  dribbling:               'Dribble',
  goal_ratio:              'Ratio buts',
  passing:                 'Passe',
  pass_accuracy:           'Précision passe',
  carries:                 'Portée balle',
  defending:               'Défense',
  mentality_interceptions: 'Interceptions',
  duel_win_rate:           'Duels gagnés',
  pressings:               'Pressing',
  goalkeeping_diving:      'Plongeon',
  goalkeeping_handling:    'Mains',
  goalkeeping_kicking:     'Dégagement',
  goalkeeping_positioning: 'Positionnement GK',
  goalkeeping_reflexes:    'Réflexes',
}

const FEATURE_GROUPS = [
  { label: 'Physique',            color: '#1e40af', features: ['pace', 'physic', 'power_stamina'] },
  { label: 'Technique',           color: '#c8102e', features: ['shooting', 'dribbling', 'goal_ratio'] },
  { label: 'Passes & Vision',     color: '#6d28d9', features: ['passing', 'pass_accuracy', 'carries'] },
  { label: 'Défense & Pressing',  color: '#1a4d2e', features: ['defending', 'mentality_interceptions', 'duel_win_rate', 'pressings'] },
  { label: 'Gardien',             color: '#d4af37', features: ['goalkeeping_diving', 'goalkeeping_handling', 'goalkeeping_kicking', 'goalkeeping_positioning', 'goalkeeping_reflexes'] },
]

const RADAR_KEYS = [
  'pace', 'shooting', 'passing', 'dribbling', 'defending', 'physic',
  'power_stamina', 'mentality_interceptions', 'pass_accuracy',
  'duel_win_rate', 'pressings', 'carries', 'goal_ratio',
]

const RADAR_SHORT = {
  pace: 'Vitesse', shooting: 'Tir', passing: 'Passe', dribbling: 'Dribble',
  defending: 'Défense', physic: 'Physique', power_stamina: 'Endurance',
  mentality_interceptions: 'Interceptions', pass_accuracy: 'Précision',
  duel_win_rate: 'Duels', pressings: 'Pressing', carries: 'Portée',
  goal_ratio: 'Buts',
}

const BASE_VECTOR = {
  pace: 0.80, shooting: 0.70, passing: 0.82, dribbling: 0.78,
  defending: 0.72, physic: 0.80, power_stamina: 0.88,
  mentality_interceptions: 0.78, goalkeeping_diving: 0.85,
  goalkeeping_handling: 0.82, goalkeeping_kicking: 0.78,
  goalkeeping_positioning: 0.83, goalkeeping_reflexes: 0.87,
  pass_accuracy: 0.85, duel_win_rate: 0.70, pressings: 0.88,
  carries: 0.80, goal_ratio: 0.72,
}

const SCENARIOS = {
  'Équilibré':      { ...BASE_VECTOR },
  'Offensif':       { ...BASE_VECTOR, pace: 1.0, shooting: 1.0, dribbling: 0.95, goal_ratio: 1.0, carries: 0.90, defending: 0.40, mentality_interceptions: 0.45, duel_win_rate: 0.45, pressings: 0.55 },
  'Défensif':       { ...BASE_VECTOR, defending: 1.0, physic: 1.0, mentality_interceptions: 1.0, duel_win_rate: 0.95, pressings: 1.0, shooting: 0.30, goal_ratio: 0.30, dribbling: 0.50, pace: 0.65 },
  'Pressing':       { ...BASE_VECTOR, pressings: 1.0, power_stamina: 1.0, mentality_interceptions: 0.95, pace: 0.95, physic: 0.90, dribbling: 0.70, shooting: 0.65 },
  'Contre-attaque': { ...BASE_VECTOR, pace: 1.0, carries: 1.0, goal_ratio: 1.0, shooting: 0.85, passing: 0.55, pass_accuracy: 0.55, pressings: 0.50, power_stamina: 0.70 },
  'Possession':     { ...BASE_VECTOR, passing: 1.0, pass_accuracy: 1.0, dribbling: 0.95, carries: 0.95, pace: 0.55, physic: 0.65, shooting: 0.55, goal_ratio: 0.55 },
}

const SCENARIO_COLORS = {
  'Équilibré': '#6b7280', 'Offensif': '#c8102e', 'Défensif': '#1a4d2e',
  'Pressing': '#1e40af', 'Contre-attaque': '#d4af37', 'Possession': '#6d28d9',
}

const POSTE_POSITIONS = {
  "4-3-3":   { GKP: [{x:50,y:92}], DEF: [{x:15,y:75},{x:38,y:78},{x:62,y:78},{x:85,y:75}], MIL: [{x:30,y:55},{x:50,y:50},{x:70,y:55}], ATT: [{x:20,y:25},{x:50,y:18},{x:80,y:25}] },
  "4-4-2":   { GKP: [{x:50,y:92}], DEF: [{x:15,y:75},{x:38,y:78},{x:62,y:78},{x:85,y:75}], MIL: [{x:15,y:50},{x:38,y:52},{x:62,y:52},{x:85,y:50}], ATT: [{x:35,y:20},{x:65,y:20}] },
  "4-2-3-1": { GKP: [{x:50,y:92}], DEF: [{x:15,y:75},{x:38,y:78},{x:62,y:78},{x:85,y:75}], MIL: [{x:35,y:58},{x:65,y:58},{x:20,y:38},{x:50,y:40},{x:80,y:38}], ATT: [{x:50,y:18}] },
  "3-5-2":   { GKP: [{x:50,y:92}], DEF: [{x:25,y:78},{x:50,y:80},{x:75,y:78}], MIL: [{x:10,y:55},{x:32,y:50},{x:50,y:48},{x:68,y:50},{x:90,y:55}], ATT: [{x:35,y:20},{x:65,y:20}] },
  "3-4-3":   { GKP: [{x:50,y:92}], DEF: [{x:25,y:78},{x:50,y:80},{x:75,y:78}], MIL: [{x:18,y:55},{x:40,y:55},{x:60,y:55},{x:82,y:55}], ATT: [{x:20,y:25},{x:50,y:18},{x:80,y:25}] },
  "5-3-2":   { GKP: [{x:50,y:92}], DEF: [{x:10,y:72},{x:30,y:78},{x:50,y:80},{x:70,y:78},{x:90,y:72}], MIL: [{x:30,y:52},{x:50,y:50},{x:70,y:52}], ATT: [{x:35,y:22},{x:65,y:22}] },
}

// ─────────────────────────────────────────────
// COMPOSANTS UTILITAIRES
// ─────────────────────────────────────────────

function SelectField({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block font-mono text-[10px] tracking-widest uppercase text-ink/50 mb-2">
        {label}
      </label>
      <div className="relative">
        <select
          value={value}
          onChange={e => onChange(e.target.value)}
          className="w-full appearance-none border border-ink/20 bg-cream px-4 py-3 pr-10 text-sm font-medium focus:outline-none focus:border-accent"
        >
          {options.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <ChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink/40" />
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────
// BARRE DE SCÉNARIOS
// ─────────────────────────────────────────────

function ScenarioBar({ active, onSelect }) {
  return (
    <div className="flex flex-wrap gap-2 mb-8">
      {Object.keys(SCENARIOS).map(name => {
        const isActive = active === name
        const color = SCENARIO_COLORS[name]
        return (
          <button
            key={name}
            onClick={() => onSelect(name)}
            className="px-4 py-2 text-xs uppercase tracking-widest font-medium border transition-all"
            style={{
              borderColor: isActive ? color : 'rgba(10,10,10,0.15)',
              background:  isActive ? color : 'transparent',
              color:       isActive ? '#fff' : 'rgba(10,10,10,0.6)',
            }}
          >
            {name}
          </button>
        )
      })}
    </div>
  )
}

// ─────────────────────────────────────────────
// PANNEAU SLIDERS
// ─────────────────────────────────────────────

function SliderPanel({ vector, onChange }) {
  const [gkpOpen, setGkpOpen] = useState(false)

  return (
    <div className="space-y-6">
      {FEATURE_GROUPS.map(group => {
        const isGkp = group.label === 'Gardien'
        const isOpen = !isGkp || gkpOpen

        return (
          <div key={group.label}>
            <button
              className="flex items-center justify-between w-full mb-3 group"
              onClick={() => isGkp && setGkpOpen(v => !v)}
            >
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ background: group.color }} />
                <span className="font-mono text-[10px] tracking-widest uppercase text-ink/60">
                  {group.label}
                </span>
              </div>
              {isGkp && (
                isOpen
                  ? <ChevronUp className="w-3.5 h-3.5 text-ink/40" />
                  : <ChevronDown className="w-3.5 h-3.5 text-ink/40" />
              )}
            </button>

            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden space-y-3"
                >
                  {group.features.map(feat => (
                    <SliderRow
                      key={feat}
                      feature={feat}
                      value={vector[feat] ?? 0.5}
                      color={group.color}
                      onChange={onChange}
                    />
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )
      })}
    </div>
  )
}

function SliderRow({ feature, value, color, onChange }) {
  return (
    <div className="flex items-center gap-3">
      <span className="font-mono text-[10px] text-ink/60 w-28 truncate shrink-0">
        {LABELS[feature]}
      </span>
      <div className="flex-1 relative flex items-center">
        <div className="w-full h-1 bg-ink/10 rounded-full absolute" />
        <div
          className="h-1 rounded-full absolute left-0"
          style={{ width: `${value * 100}%`, background: color, opacity: 0.6 }}
        />
        <input
          type="range"
          min="0" max="1" step="0.01"
          value={value}
          onChange={e => onChange(feature, parseFloat(e.target.value))}
          className="w-full h-1 appearance-none bg-transparent relative z-10 cursor-pointer"
          style={{ accentColor: color }}
        />
      </div>
      <span className="font-mono text-xs w-8 text-right shrink-0"
            style={{ color }}>
        {value.toFixed(2)}
      </span>
    </div>
  )
}

// ─────────────────────────────────────────────
// RADAR LIVE
// ─────────────────────────────────────────────

function LiveRadar({ vector }) {
  const radarData = RADAR_KEYS.map(k => ({
    label: RADAR_SHORT[k],
    value: vector[k] ?? 0,
  }))

  return (
    <div className="border border-ink/10 bg-white p-4">
      <div className="font-mono text-[10px] tracking-widest uppercase text-ink/50 mb-2">
        / Profil tactique
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="rgba(10,10,10,0.1)" />
          <PolarAngleAxis
            dataKey="label"
            tick={{ fontSize: 7, fill: 'rgba(10,10,10,0.5)' }}
          />
          <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
          <Radar
            dataKey="value"
            stroke="#c8102e"
            fill="#c8102e"
            fillOpacity={0.25}
            strokeWidth={1.5}
            isAnimationActive={false}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

// ─────────────────────────────────────────────
// TERRAIN AVEC BADGES IN/OUT
// ─────────────────────────────────────────────

function EditorPitch({ players, formation }) {
  const POSITIONS = POSTE_POSITIONS[formation] || POSTE_POSITIONS['4-3-3']
  const byPoste = { GKP: [], DEF: [], MIL: [], ATT: [] }
  players.forEach(p => byPoste[p.poste]?.push(p))

  return (
    <div className="relative aspect-[2/3] bg-[#1a4d2e] rounded-sm overflow-hidden shadow-xl">
      <PitchLines />
      {players.map((p, i) => {
        const idx = byPoste[p.poste].indexOf(p)
        const pos = POSITIONS[p.poste]?.[idx]
        if (!pos) return null
        return (
          <PlayerDot key={p.short_name} player={p} x={pos.x} y={pos.y} delay={i * 0.06} />
        )
      })}
    </div>
  )
}

function PitchLines() {
  return (
    <svg viewBox="0 0 100 150" className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
      <rect x="2" y="2" width="96" height="146" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
      <line x1="2" y1="75" x2="98" y2="75" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
      <circle cx="50" cy="75" r="9" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
      <rect x="25" y="2" width="50" height="18" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
      <rect x="35" y="2" width="30" height="8" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
      <rect x="25" y="130" width="50" height="18" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
      <rect x="35" y="140" width="30" height="8" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
    </svg>
  )
}

function PlayerDot({ player, x, y, delay }) {
  const ringColor = player.is_new ? '#22c55e' : 'rgba(200,16,46,0.9)'

  return (
    <motion.div
      key={player.short_name}
      initial={{ opacity: 0, scale: 0.5 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.35, type: 'spring', stiffness: 200 }}
      className="absolute -translate-x-1/2 -translate-y-1/2 group cursor-default"
      style={{ left: `${x}%`, top: `${y}%` }}
    >
      <div className="flex flex-col items-center">
        {/* Badge IN */}
        {player.is_new && (
          <div className="mb-0.5 px-1.5 py-0 bg-green-500 text-white text-[8px] font-bold tracking-wider rounded-sm">
            IN
          </div>
        )}
        <div
          className="w-10 h-10 rounded-full bg-cream flex items-center justify-center font-display text-sm shadow-lg"
          style={{ border: `2px solid ${ringColor}` }}
        >
          {player.overall}
        </div>
        <div className="mt-0.5 px-1.5 py-0.5 bg-ink/80 text-cream text-[8px] font-medium whitespace-nowrap rounded-sm max-w-[60px] truncate text-center">
          {player.short_name.split(' ').pop()}
        </div>
        <div className="mt-0.5 font-mono text-[7px] text-white/70">
          {player.custom_score.toFixed(3)}
        </div>
      </div>

      {/* Tooltip */}
      <div className="absolute left-1/2 -translate-x-1/2 -bottom-16 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity bg-ink text-cream px-3 py-2 text-[10px] rounded-sm whitespace-nowrap z-10 shadow-xl">
        <div className="font-medium">{player.short_name}</div>
        <div className="text-cream/60">{player.club}</div>
        <div className="text-accent font-mono mt-1">Score: {player.custom_score}</div>
        {player.is_new && <div className="text-green-400 mt-0.5">Nouveau !</div>}
      </div>
    </motion.div>
  )
}

// ─────────────────────────────────────────────
// DELTA BANNER
// ─────────────────────────────────────────────

function DeltaBanner({ composition }) {
  if (!composition) return null
  const { entrants, sortants, total_score, original_total } = composition
  const diff = total_score - original_total
  const hasDelta = entrants.length > 0 || sortants.length > 0

  return (
    <div className="border border-ink/10 bg-ink text-cream p-5 space-y-4">
      {/* Score */}
      <div className="flex items-end justify-between">
        <div>
          <div className="font-mono text-[9px] tracking-widest uppercase text-cream/40 mb-1">
            Score cosinus total
          </div>
          <div className="font-display text-4xl text-accent leading-none">
            {total_score.toFixed(4)}
          </div>
        </div>
        <div className="text-right">
          <div className="font-mono text-[9px] tracking-widest uppercase text-cream/40 mb-1">
            vs composition GNN
          </div>
          <div className={`font-mono text-sm font-semibold ${diff > 0 ? 'text-green-400' : diff < 0 ? 'text-red-400' : 'text-cream/50'}`}>
            {diff > 0 ? '▲' : diff < 0 ? '▼' : '—'} {diff > 0 ? '+' : ''}{diff.toFixed(4)}
          </div>
        </div>
      </div>

      {/* Changements */}
      {hasDelta ? (
        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-cream/10">
          <div>
            <div className="font-mono text-[9px] tracking-widest uppercase text-green-400 mb-2">
              Entrants ({entrants.length})
            </div>
            {entrants.length === 0
              ? <span className="text-cream/30 text-xs">—</span>
              : entrants.map(n => (
                  <div key={n} className="text-xs text-green-300 mb-1 flex items-center gap-1.5">
                    <span className="text-green-500 text-[8px] font-bold">IN</span>
                    {n}
                  </div>
                ))
            }
          </div>
          <div>
            <div className="font-mono text-[9px] tracking-widest uppercase text-red-400 mb-2">
              Sortants ({sortants.length})
            </div>
            {sortants.length === 0
              ? <span className="text-cream/30 text-xs">—</span>
              : sortants.map(n => (
                  <div key={n} className="text-xs text-red-300 mb-1 flex items-center gap-1.5">
                    <span className="text-red-500 text-[8px] font-bold">OUT</span>
                    {n}
                  </div>
                ))
            }
          </div>
        </div>
      ) : (
        <div className="pt-3 border-t border-cream/10">
          <span className="font-mono text-[10px] text-cream/30 uppercase tracking-widest">
            Composition identique à la référence GNN
          </span>
        </div>
      )}
    </div>
  )
}

// ─────────────────────────────────────────────
// LISTE JOUEURS (panneau droite)
// ─────────────────────────────────────────────

function PlayersList({ players }) {
  const grouped = { GKP: [], DEF: [], MIL: [], ATT: [] }
  players.forEach(p => grouped[p.poste]?.push(p))

  const POSTE_LABELS = { GKP: 'Gardien', DEF: 'Défenseurs', MIL: 'Milieux', ATT: 'Attaquants' }
  const POSTE_COLORS = { GKP: '#d4af37', DEF: '#1a4d2e', MIL: '#1e40af', ATT: '#c8102e' }

  return (
    <div className="space-y-4">
      {['GKP', 'DEF', 'MIL', 'ATT'].map(poste => (
        <div key={poste}>
          <h3 className="font-mono text-[9px] tracking-widest uppercase mb-2"
              style={{ color: POSTE_COLORS[poste] }}>
            {POSTE_LABELS[poste]}
          </h3>
          <div className="space-y-px">
            {grouped[poste].map((p, i) => (
              <motion.div
                key={p.short_name}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.04 }}
                className={`p-2.5 flex items-center justify-between border transition-colors ${
                  p.is_new
                    ? 'bg-green-50 border-green-200'
                    : 'bg-white border-ink/10'
                }`}
              >
                <div className="flex items-center gap-2">
                  {p.is_new && (
                    <span className="text-[8px] font-bold bg-green-500 text-white px-1 rounded-sm">IN</span>
                  )}
                  <div>
                    <div className="text-sm font-medium">{p.short_name}</div>
                    <div className="text-[10px] text-ink/50">{p.club}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-display text-xl leading-none">{p.overall}</div>
                  <div className="font-mono text-[9px] text-accent">{p.custom_score}</div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────
// PAGE PRINCIPALE
// ─────────────────────────────────────────────

export default function PFAEditor() {
  const [pfaVector, setPfaVector]         = useState(BASE_VECTOR)
  const [activeScenario, setActiveScenario] = useState('Équilibré')
  const [nation, setNation]               = useState('Morocco')
  const [formation, setFormation]         = useState('4-3-3')
  const [nations, setNations]             = useState([])
  const [composition, setComposition]     = useState(null)
  const [loading, setLoading]             = useState(false)
  const [error, setError]                 = useState(null)
  const debounceRef                       = useRef(null)

  // Charger la liste des nations
  useEffect(() => {
    getNationsList(11).then(d => setNations(d.nations || [])).catch(() => {})
  }, [])

  // Charger le vecteur default depuis le serveur (une seule fois)
  useEffect(() => {
    getEditorDefaultVector()
      .then(v => {
        setPfaVector(v)
        SCENARIOS['Équilibré'] = { ...v }
      })
      .catch(() => {}) // fallback sur BASE_VECTOR déjà en état
  }, [])

  // Recalcul debouncé quand le vecteur, la nation ou la formation change
  const fetchComposition = useCallback((vector, nat, form) => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setLoading(true)
      setError(null)
      postEditorComposition(vector, nat || null, form)
        .then(data => setComposition(data))
        .catch(e => setError(e?.response?.data?.detail || 'Erreur'))
        .finally(() => setLoading(false))
    }, 250)
  }, [])

  useEffect(() => {
    fetchComposition(pfaVector, nation, formation)
  }, [pfaVector, nation, formation, fetchComposition])

  // Modifier un slider
  const handleSliderChange = useCallback((feature, value) => {
    setActiveScenario(null)
    setPfaVector(prev => ({ ...prev, [feature]: value }))
  }, [])

  // Sélectionner un scénario
  const handleScenario = useCallback((name) => {
    setActiveScenario(name)
    setPfaVector({ ...SCENARIOS[name] })
  }, [])

  // Réinitialiser
  const handleReset = useCallback(() => {
    setActiveScenario('Équilibré')
    setPfaVector({ ...SCENARIOS['Équilibré'] })
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">

      {/* HEADER */}
      <div className="mb-10">
        <div className="font-mono text-xs tracking-widest uppercase text-accent mb-4">
          / Éditeur PFA
        </div>
        <h1 className="font-display text-5xl md:text-7xl tracking-tight">
          Vecteur <span className="text-accent">interactif</span>
        </h1>
        <p className="mt-4 text-ink/70 max-w-2xl">
          Ajustez les 18 dimensions du profil tactique idéal. La composition se recalcule
          instantanément par similarité cosinus entre les attributs des joueurs et votre vecteur.
        </p>
      </div>

      {/* SCÉNARIOS */}
      <ScenarioBar active={activeScenario} onSelect={handleScenario} />

      {/* SÉLECTEURS */}
      <div className="grid md:grid-cols-2 gap-4 mb-8">
        <SelectField
          label="Nation"
          value={nation}
          onChange={v => { setNation(v); setComposition(null) }}
          options={[
            { value: '', label: '🌍 Monde (toutes nations)' },
            ...nations.map(n => ({ value: n.nation, label: `${n.nation} (${n.players_count})` }))
          ]}
        />
        <SelectField
          label="Formation"
          value={formation}
          onChange={v => { setFormation(v); setComposition(null) }}
          options={FORMATIONS.map(f => ({ value: f, label: f }))}
        />
      </div>

      {/* CONTENU PRINCIPAL */}
      <div className="grid lg:grid-cols-[340px_1fr] gap-8">

        {/* ── COLONNE GAUCHE : Sliders + Radar ── */}
        <div className="space-y-6">
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono text-[10px] tracking-widest uppercase text-ink/50">
              / Paramètres
            </span>
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-ink/50 hover:text-accent transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              Réinitialiser
            </button>
          </div>

          <SliderPanel vector={pfaVector} onChange={handleSliderChange} />

          <LiveRadar vector={pfaVector} />
        </div>

        {/* ── COLONNE DROITE : Terrain + Delta + Liste ── */}
        <div className="space-y-6">

          {/* Indicateur de chargement sur le terrain */}
          <div className="relative">
            {loading && (
              <div className="absolute inset-0 flex items-center justify-center bg-cream/70 z-10 rounded-sm">
                <Loader className="w-5 h-5 animate-spin text-accent" />
              </div>
            )}
            <AnimatePresence mode="wait">
              {!error && composition && (
                <motion.div
                  key={`${nation}-${formation}-${activeScenario}`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div className="font-mono text-[10px] tracking-widest uppercase text-ink/50 mb-3">
                    / Terrain · {formation}
                  </div>
                  <EditorPitch players={composition.players} formation={formation} />
                </motion.div>
              )}
            </AnimatePresence>

            {error && !loading && (
              <div className="border-2 border-accent p-6 bg-accent/5">
                <div className="font-mono text-xs uppercase tracking-widest text-accent mb-1">Erreur</div>
                <div className="text-sm text-ink/80">{error}</div>
              </div>
            )}
          </div>

          {/* Delta + Score */}
          {composition && <DeltaBanner composition={composition} />}

          {/* Liste joueurs */}
          {composition && (
            <div>
              <div className="font-mono text-[10px] tracking-widest uppercase text-ink/50 mb-3">
                / Détails
              </div>
              <PlayersList players={composition.players} />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
