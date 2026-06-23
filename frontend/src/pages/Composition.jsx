import { useEffect, useState, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, ResponsiveContainer,
} from 'recharts'
import { getComposition, getNationsList, postEditorComposition } from '../services/api'
import { Loader, ChevronDown, ChevronUp, RotateCcw, SlidersHorizontal } from 'lucide-react'

// ─────────────────────────────────────────────
// CONSTANTES
// ─────────────────────────────────────────────

const FORMATIONS = ['4-3-3', '4-4-2', '4-2-3-1', '3-5-2', '3-4-3', '5-3-2']

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

const LABELS = {
  pace: 'Vitesse', physic: 'Physique', power_stamina: 'Endurance',
  shooting: 'Tir', dribbling: 'Dribble', goal_ratio: 'Ratio buts',
  passing: 'Passe', pass_accuracy: 'Précision passe', carries: 'Portée balle',
  defending: 'Défense', mentality_interceptions: 'Interceptions',
  duel_win_rate: 'Duels gagnés', pressings: 'Pressing',
  goalkeeping_diving: 'Plongeon', goalkeeping_handling: 'Mains',
  goalkeeping_kicking: 'Dégagement', goalkeeping_positioning: 'Position. GK',
  goalkeeping_reflexes: 'Réflexes',
}

const FEATURE_GROUPS = [
  { label: 'Physique',           color: '#1e40af', features: ['pace', 'physic', 'power_stamina'] },
  { label: 'Technique',          color: '#c8102e', features: ['shooting', 'dribbling', 'goal_ratio'] },
  { label: 'Passes & Vision',    color: '#6d28d9', features: ['passing', 'pass_accuracy', 'carries'] },
  { label: 'Défense & Pressing', color: '#1a4d2e', features: ['defending', 'mentality_interceptions', 'duel_win_rate', 'pressings'] },
  { label: 'Gardien',            color: '#d4af37', features: ['goalkeeping_diving', 'goalkeeping_handling', 'goalkeeping_kicking', 'goalkeeping_positioning', 'goalkeeping_reflexes'] },
]

const RADAR_KEYS = ['pace','shooting','passing','dribbling','defending','physic',
  'power_stamina','mentality_interceptions','pass_accuracy','duel_win_rate','pressings','carries','goal_ratio']

const RADAR_SHORT = {
  pace:'Vitesse', shooting:'Tir', passing:'Passe', dribbling:'Dribble',
  defending:'Défense', physic:'Physique', power_stamina:'Endurance',
  mentality_interceptions:'Interceptions', pass_accuracy:'Précision',
  duel_win_rate:'Duels', pressings:'Pressing', carries:'Portée', goal_ratio:'Buts',
}

const POSTE_POSITIONS = {
  "4-3-3":   { GKP:[{x:50,y:92}], DEF:[{x:15,y:75},{x:38,y:78},{x:62,y:78},{x:85,y:75}], MIL:[{x:30,y:55},{x:50,y:50},{x:70,y:55}], ATT:[{x:20,y:25},{x:50,y:18},{x:80,y:25}] },
  "4-4-2":   { GKP:[{x:50,y:92}], DEF:[{x:15,y:75},{x:38,y:78},{x:62,y:78},{x:85,y:75}], MIL:[{x:15,y:50},{x:38,y:52},{x:62,y:52},{x:85,y:50}], ATT:[{x:35,y:20},{x:65,y:20}] },
  "4-2-3-1": { GKP:[{x:50,y:92}], DEF:[{x:15,y:75},{x:38,y:78},{x:62,y:78},{x:85,y:75}], MIL:[{x:35,y:58},{x:65,y:58},{x:20,y:38},{x:50,y:40},{x:80,y:38}], ATT:[{x:50,y:18}] },
  "3-5-2":   { GKP:[{x:50,y:92}], DEF:[{x:25,y:78},{x:50,y:80},{x:75,y:78}], MIL:[{x:10,y:55},{x:32,y:50},{x:50,y:48},{x:68,y:50},{x:90,y:55}], ATT:[{x:35,y:20},{x:65,y:20}] },
  "3-4-3":   { GKP:[{x:50,y:92}], DEF:[{x:25,y:78},{x:50,y:80},{x:75,y:78}], MIL:[{x:18,y:55},{x:40,y:55},{x:60,y:55},{x:82,y:55}], ATT:[{x:20,y:25},{x:50,y:18},{x:80,y:25}] },
  "5-3-2":   { GKP:[{x:50,y:92}], DEF:[{x:10,y:72},{x:30,y:78},{x:50,y:80},{x:70,y:78},{x:90,y:72}], MIL:[{x:30,y:52},{x:50,y:50},{x:70,y:52}], ATT:[{x:35,y:22},{x:65,y:22}] },
}

// ─────────────────────────────────────────────
// SELECT
// ─────────────────────────────────────────────

function Select({ label, value, onChange, options }) {
  return (
    <label className="block">
      <span className="text-[10px] uppercase tracking-widest text-ink/60 font-medium">{label}</span>
      <div className="relative mt-2">
        <select
          value={value}
          onChange={e => onChange(e.target.value)}
          className="w-full bg-white border border-ink/20 px-4 py-3 font-medium appearance-none focus:border-accent focus:outline-none transition"
        >
          {options.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink/40 pointer-events-none" />
      </div>
    </label>
  )
}

// ─────────────────────────────────────────────
// BARRE DE SCÉNARIOS
// ─────────────────────────────────────────────

function ScenarioBar({ active, onSelect }) {
  return (
    <div className="flex flex-wrap gap-2">
      {Object.keys(SCENARIOS).map(name => {
        const isActive = active === name
        const color = SCENARIO_COLORS[name]
        return (
          <button
            key={name}
            onClick={() => onSelect(name)}
            className="px-3 py-1.5 text-[10px] uppercase tracking-widest font-medium border transition-all"
            style={{
              borderColor: isActive ? color : 'rgba(10,10,10,0.15)',
              background:  isActive ? color : 'transparent',
              color:       isActive ? '#fff' : 'rgba(10,10,10,0.55)',
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
// SLIDERS
// ─────────────────────────────────────────────

function SliderPanel({ vector, onChange }) {
  const [gkpOpen, setGkpOpen] = useState(false)

  return (
    <div className="space-y-5">
      {FEATURE_GROUPS.map(group => {
        const isGkp = group.label === 'Gardien'
        const isOpen = !isGkp || gkpOpen

        return (
          <div key={group.label}>
            <button
              className="flex items-center justify-between w-full mb-2.5"
              onClick={() => isGkp && setGkpOpen(v => !v)}
            >
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full" style={{ background: group.color }} />
                <span className="font-mono text-[9px] tracking-widest uppercase text-ink/50">
                  {group.label}
                </span>
              </div>
              {isGkp && (
                isOpen
                  ? <ChevronUp className="w-3 h-3 text-ink/30" />
                  : <ChevronDown className="w-3 h-3 text-ink/30" />
              )}
            </button>

            <AnimatePresence initial={false}>
              {isOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.18 }}
                  className="overflow-hidden space-y-2.5"
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
    <div className="flex items-center gap-2">
      <span className="font-mono text-[9px] text-ink/55 w-24 truncate shrink-0">
        {LABELS[feature]}
      </span>
      <div className="flex-1 relative flex items-center h-4">
        <div className="w-full h-0.5 bg-ink/10 rounded-full absolute" />
        <div
          className="h-0.5 rounded-full absolute left-0 transition-all"
          style={{ width: `${value * 100}%`, background: color, opacity: 0.5 }}
        />
        <input
          type="range" min="0" max="1" step="0.01"
          value={value}
          onChange={e => onChange(feature, parseFloat(e.target.value))}
          className="w-full h-0.5 appearance-none bg-transparent relative z-10 cursor-pointer"
          style={{ accentColor: color }}
        />
      </div>
      <span className="font-mono text-[9px] w-7 text-right shrink-0 tabular-nums"
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
  const data = RADAR_KEYS.map(k => ({ label: RADAR_SHORT[k], value: vector[k] ?? 0 }))

  return (
    <div className="border border-ink/10 bg-white p-3 mt-5">
      <div className="font-mono text-[9px] tracking-widest uppercase text-ink/40 mb-1">
        / Profil tactique
      </div>
      <ResponsiveContainer width="100%" height={180}>
        <RadarChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 8 }}>
          <PolarGrid stroke="rgba(10,10,10,0.08)" />
          <PolarAngleAxis dataKey="label" tick={{ fontSize: 6.5, fill: 'rgba(10,10,10,0.45)' }} />
          <PolarRadiusAxis domain={[0, 1]} tick={false} axisLine={false} />
          <Radar dataKey="value" stroke="#c8102e" fill="#c8102e" fillOpacity={0.2}
                 strokeWidth={1.5} isAnimationActive={false} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

// ─────────────────────────────────────────────
// TERRAIN
// ─────────────────────────────────────────────

function Pitch({ players, formation, isEditorMode }) {
  const POSITIONS = POSTE_POSITIONS[formation] || POSTE_POSITIONS['4-3-3']
  const byPoste = { GKP: [], DEF: [], MIL: [], ATT: [] }
  players.forEach(p => byPoste[p.poste]?.push(p))

  return (
    <div className="relative aspect-[2/3] bg-[#1a4d2e] rounded-sm overflow-hidden shadow-2xl">
      <PitchLines />
      {players.map((p, i) => {
        const idx = byPoste[p.poste].indexOf(p)
        const pos = POSITIONS[p.poste]?.[idx]
        if (!pos) return null
        return (
          <PlayerDot
            key={p.short_name}
            player={p}
            x={pos.x} y={pos.y}
            delay={i * 0.07}
            isEditorMode={isEditorMode}
          />
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
      <circle cx="50" cy="75" r="0.5" fill="rgba(255,255,255,0.4)"/>
      <rect x="25" y="2" width="50" height="18" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
      <rect x="35" y="2" width="30" height="8" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
      <rect x="25" y="130" width="50" height="18" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
      <rect x="35" y="140" width="30" height="8" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="0.3"/>
    </svg>
  )
}

function PlayerDot({ player, x, y, delay, isEditorMode }) {
  const isNew    = isEditorMode && player.is_new
  const ringColor = isNew ? '#22c55e' : 'rgba(200,16,46,0.9)'
  const score    = isEditorMode
    ? (player.custom_score?.toFixed(3) ?? player.pfa_score)
    : player.pfa_score

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay, duration: 0.45, type: 'spring', stiffness: 180 }}
      className="absolute -translate-x-1/2 -translate-y-1/2 group cursor-default"
      style={{ left: `${x}%`, top: `${y}%` }}
    >
      <div className="flex flex-col items-center">
        {isNew && (
          <div className="mb-0.5 px-1.5 bg-green-500 text-white text-[7px] font-bold tracking-wider rounded-sm">
            IN
          </div>
        )}
        <div
          className="w-10 h-10 md:w-11 md:h-11 rounded-full bg-cream flex items-center justify-center font-display text-sm shadow-lg group-hover:scale-110 transition-transform"
          style={{ border: `2px solid ${ringColor}` }}
        >
          {player.overall}
        </div>
        <div className="mt-0.5 px-1.5 py-0.5 bg-ink/80 text-cream text-[8px] font-medium tracking-tight whitespace-nowrap rounded-sm max-w-[58px] truncate text-center">
          {player.short_name.split(' ').pop()}
        </div>
        {isEditorMode && (
          <div className="mt-0.5 font-mono text-[7px] text-white/60">{score}</div>
        )}
      </div>
      {/* Tooltip */}
      <div className="absolute left-1/2 -translate-x-1/2 -bottom-16 opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity bg-ink text-cream px-3 py-2 text-[10px] rounded-sm whitespace-nowrap z-10 shadow-xl">
        <div className="font-medium">{player.short_name}</div>
        <div className="text-cream/60">{player.club}</div>
        <div className="text-accent font-mono mt-1">
          {isEditorMode ? `Score: ${score}` : `PFA: ${player.pfa_score}`}
        </div>
        {isNew && <div className="text-green-400">Nouveau joueur</div>}
      </div>
    </motion.div>
  )
}

// ─────────────────────────────────────────────
// PANNEAU DROITE
// ─────────────────────────────────────────────

function ScorePanel({ total }) {
  return (
    <div className="bg-ink text-cream p-5">
      <div className="text-[9px] uppercase tracking-widest text-cream/50">Score PFA · GNN</div>
      <div className="font-display text-5xl text-accent mt-1">{total.toFixed(4)}</div>
    </div>
  )
}

function DeltaBanner({ data }) {
  const { entrants, sortants, total_score, original_total } = data
  const diff   = total_score - original_total
  const noChange = entrants.length === 0 && sortants.length === 0

  return (
    <div className="bg-ink text-cream p-5 space-y-3">
      {/* Scores */}
      <div className="flex items-end justify-between">
        <div>
          <div className="text-[9px] uppercase tracking-widest text-cream/40 mb-0.5">Score cosinus</div>
          <div className="font-display text-4xl text-accent leading-none">{total_score.toFixed(4)}</div>
        </div>
        <div className="text-right">
          <div className="text-[9px] uppercase tracking-widest text-cream/40 mb-0.5">vs GNN</div>
          <div className={`font-mono text-sm font-semibold ${diff > 0 ? 'text-green-400' : diff < 0 ? 'text-red-400' : 'text-cream/40'}`}>
            {diff > 0 ? '▲ +' : diff < 0 ? '▼ ' : '— '}{diff.toFixed(4)}
          </div>
        </div>
      </div>

      {/* Delta */}
      {!noChange ? (
        <div className="grid grid-cols-2 gap-3 pt-3 border-t border-cream/10">
          <div>
            <div className="font-mono text-[8px] tracking-widest uppercase text-green-400 mb-1.5">
              Entrants ({entrants.length})
            </div>
            {entrants.map(n => (
              <div key={n} className="text-[11px] text-green-300 mb-0.5 flex items-center gap-1">
                <span className="text-[7px] font-bold bg-green-500 text-white px-1 rounded-sm">IN</span>
                {n}
              </div>
            ))}
          </div>
          <div>
            <div className="font-mono text-[8px] tracking-widest uppercase text-red-400 mb-1.5">
              Sortants ({sortants.length})
            </div>
            {sortants.map(n => (
              <div key={n} className="text-[11px] text-red-300 mb-0.5 flex items-center gap-1">
                <span className="text-[7px] font-bold bg-red-500 text-white px-1 rounded-sm">OUT</span>
                {n}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="pt-3 border-t border-cream/10">
          <span className="font-mono text-[9px] text-cream/30 uppercase tracking-widest">
            Composition identique à la référence GNN
          </span>
        </div>
      )}
    </div>
  )
}

function PlayersList({ players, isEditorMode }) {
  const grouped = { GKP: [], DEF: [], MIL: [], ATT: [] }
  players.forEach(p => grouped[p.poste]?.push(p))
  const POSTE_LABELS = { GKP: 'Gardien', DEF: 'Défenseurs', MIL: 'Milieux', ATT: 'Attaquants' }
  const POSTE_COLORS = { GKP: '#d4af37', DEF: '#1a4d2e', MIL: '#1e40af', ATT: '#c8102e' }

  return (
    <div className="space-y-5">
      {['GKP','DEF','MIL','ATT'].map(poste => (
        <div key={poste}>
          <h3 className="font-mono text-[9px] tracking-widest uppercase mb-2"
              style={{ color: POSTE_COLORS[poste] }}>
            {POSTE_LABELS[poste]}
          </h3>
          <div className="space-y-px">
            {grouped[poste].map((p, i) => {
              const isNew   = isEditorMode && p.is_new
              const score   = isEditorMode ? p.custom_score : p.pfa_score
              return (
                <motion.div
                  key={p.short_name}
                  initial={{ opacity: 0, x: -16 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className={`p-3 flex items-center justify-between border transition-colors ${
                    isNew ? 'bg-green-50 border-green-200' : 'bg-white border-ink/10 hover:border-accent'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    {isNew && (
                      <span className="text-[7px] font-bold bg-green-500 text-white px-1 rounded-sm shrink-0">IN</span>
                    )}
                    <div className="min-w-0">
                      <div className="font-medium text-sm truncate">{p.short_name}</div>
                      <div className="text-[10px] text-ink/50 truncate">{p.club}</div>
                    </div>
                  </div>
                  <div className="text-right shrink-0 ml-2">
                    <div className="font-display text-2xl leading-none">{p.overall}</div>
                    <div className="font-mono text-[9px] text-accent">{score}</div>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────
// PAGE PRINCIPALE
// ─────────────────────────────────────────────

export default function Composition() {
  const [nation, setNation]               = useState('Morocco')
  const [formation, setFormation]         = useState('4-3-3')
  const [nations, setNations]             = useState([])
  const [pfaVector, setPfaVector]         = useState(BASE_VECTOR)
  const [activeScenario, setActiveScenario] = useState('Équilibré')
  const [isEditorOpen, setIsEditorOpen]   = useState(false)

  // Deux sources de données distinctes
  const [gnnData, setGnnData]       = useState(null)
  const [editorData, setEditorData] = useState(null)
  const [gnnLoading, setGnnLoading]     = useState(false)
  const [editorLoading, setEditorLoading] = useState(false)
  const [error, setError]           = useState(null)
  const debounceRef                 = useRef(null)

  const displayData = (isEditorOpen && editorData) ? editorData : gnnData
  const loading     = isEditorOpen ? editorLoading : gnnLoading

  // ── Nations ──
  useEffect(() => {
    getNationsList(11).then(d => setNations(d.nations || [])).catch(() => {})
  }, [])

  // ── Composition GNN (toujours à jour) ──
  useEffect(() => {
    setGnnLoading(true)
    setError(null)
    getComposition(nation || null, formation)
      .then(setGnnData)
      .catch(e => setError(e?.response?.data?.detail || 'Erreur'))
      .finally(() => setGnnLoading(false))
  }, [nation, formation])

  // ── Composition éditeur (debouncée) ──
  const fetchEditor = useCallback((vector, nat, form) => {
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setEditorLoading(true)
      postEditorComposition(vector, nat || null, form)
        .then(setEditorData)
        .catch(e => setError(e?.response?.data?.detail || 'Erreur'))
        .finally(() => setEditorLoading(false))
    }, 250)
  }, [])

  // Déclenche l'éditeur dès qu'il est ouvert ou que ses paramètres changent
  useEffect(() => {
    if (isEditorOpen) {
      fetchEditor(pfaVector, nation, formation)
    }
  }, [pfaVector, nation, formation, isEditorOpen, fetchEditor])

  // ── Handlers ──
  const handleSliderChange = useCallback((feature, value) => {
    setActiveScenario(null)
    setPfaVector(prev => ({ ...prev, [feature]: value }))
  }, [])

  const handleScenario = useCallback((name) => {
    setActiveScenario(name)
    setPfaVector({ ...SCENARIOS[name] })
    if (!isEditorOpen) setIsEditorOpen(true)
  }, [isEditorOpen])

  const handleReset = useCallback(() => {
    setActiveScenario('Équilibré')
    setPfaVector({ ...BASE_VECTOR })
    setEditorData(null)
    setIsEditorOpen(false)
  }, [])

  const handleNationChange = (v) => { setNation(v); setEditorData(null) }
  const handleFormationChange = (v) => { setFormation(v); setEditorData(null) }

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">

      {/* HEADER */}
      <div className="mb-10">
        <div className="font-mono text-xs tracking-widest uppercase text-accent mb-4">
          / Composition optimale
        </div>
        <h1 className="font-display text-5xl md:text-7xl tracking-tight">
          Le XI <span className="text-accent">parfait</span>
        </h1>
        <p className="mt-4 text-ink/70 max-w-2xl">
          Choisissez une nation, une formation et un style tactique.
          Activez l'éditeur pour ajuster finement le profil PFA et voir la composition se recalculer en direct.
        </p>
      </div>

      {/* SÉLECTEURS */}
      <div className="grid md:grid-cols-2 gap-5 mb-8">
        <Select
          label="Nation"
          value={nation}
          onChange={handleNationChange}
          options={[
            { value: '', label: '🌍 Monde (toutes nations)' },
            ...nations.map(n => ({ value: n.nation, label: `${n.nation} (${n.players_count})` }))
          ]}
        />
        <Select
          label="Formation"
          value={formation}
          onChange={handleFormationChange}
          options={FORMATIONS.map(f => ({ value: f, label: f }))}
        />
      </div>

      {/* SCÉNARIOS + TOGGLE */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <ScenarioBar active={activeScenario} onSelect={handleScenario} />

        <div className="flex items-center gap-2 shrink-0">
          {isEditorOpen && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-widest text-ink/50 hover:text-accent transition-colors px-3 py-2 border border-ink/15 hover:border-accent"
            >
              <RotateCcw className="w-3 h-3" />
              Réinit.
            </button>
          )}
          <button
            onClick={() => setIsEditorOpen(v => !v)}
            className={`flex items-center gap-2 px-4 py-2 text-[10px] uppercase tracking-widest font-mono border transition-all ${
              isEditorOpen
                ? 'bg-accent text-cream border-accent'
                : 'border-ink/20 text-ink/60 hover:border-accent hover:text-accent'
            }`}
          >
            <SlidersHorizontal className="w-3.5 h-3.5" />
            {isEditorOpen ? 'Masquer PFA' : 'Éditeur PFA'}
          </button>
        </div>
      </div>

      {/* CONTENU PRINCIPAL */}
      <div className="lg:flex gap-8 items-start">

        {/* ── PANNEAU ÉDITEUR (gauche, animé) ── */}
        <AnimatePresence>
          {isEditorOpen && (
            <motion.div
              key="editor-panel"
              initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -16 }}
              transition={{ duration: 0.25 }}
              className="w-full lg:w-[290px] lg:shrink-0 mb-8 lg:mb-0"
            >
              <div className="lg:w-[290px]">
                <div className="font-mono text-[9px] tracking-widest uppercase text-ink/40 mb-4">
                  / Vecteur PFA — {Object.values(pfaVector).reduce((a,b)=>a+b,0).toFixed(1)} pts
                </div>
                <SliderPanel vector={pfaVector} onChange={handleSliderChange} />
                <LiveRadar vector={pfaVector} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── ZONE PRINCIPALE (droite) ── */}
        <div className="flex-1 min-w-0">
          {loading && (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader className="w-7 h-7 animate-spin text-accent" />
              <div className="mt-3 font-mono text-[10px] tracking-widest uppercase text-ink/50">
                {isEditorOpen ? 'Recalcul en cours…' : 'Génération de la composition…'}
              </div>
            </div>
          )}

          {error && !loading && (
            <div className="border-2 border-accent p-6 bg-accent/5">
              <div className="font-mono text-xs uppercase tracking-widest text-accent mb-1">Erreur</div>
              <div className="text-sm text-ink/80">{error}</div>
            </div>
          )}

          <AnimatePresence mode="wait">
            {!loading && !error && displayData && (
              <motion.div
                key={`${nation}-${formation}-${isEditorOpen}`}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
                className={`grid gap-6 ${isEditorOpen ? 'xl:grid-cols-5' : 'lg:grid-cols-5'}`}
              >
                {/* Terrain */}
                <div className={isEditorOpen ? 'xl:col-span-3' : 'lg:col-span-3'}>
                  <div className="font-mono text-[10px] tracking-widest uppercase text-ink/50 mb-3">
                    / Terrain · {formation}
                    {isEditorOpen && activeScenario && (
                      <span className="ml-3" style={{ color: SCENARIO_COLORS[activeScenario] }}>
                        {activeScenario}
                      </span>
                    )}
                  </div>
                  <Pitch
                    players={displayData.players}
                    formation={formation}
                    isEditorMode={isEditorOpen}
                  />
                </div>

                {/* Panneau latéral */}
                <div className={`space-y-5 ${isEditorOpen ? 'xl:col-span-2' : 'lg:col-span-2'}`}>
                  <div className="font-mono text-[10px] tracking-widest uppercase text-ink/50">
                    / Détails
                  </div>

                  {isEditorOpen && editorData
                    ? <DeltaBanner data={editorData} />
                    : <ScorePanel total={gnnData?.total_pfa ?? 0} />
                  }

                  <PlayersList
                    players={displayData.players}
                    isEditorMode={isEditorOpen && !!editorData}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}
