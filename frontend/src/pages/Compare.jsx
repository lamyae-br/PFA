import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { searchPlayers, comparePlayers } from '../services/api'
import {
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Radar, Legend, ResponsiveContainer, Tooltip,
} from 'recharts'
import { Search, Loader, ArrowRight, X, Trophy, TrendingUp, TrendingDown } from 'lucide-react'

// ─────────────────────────────────────────
// Page principale
// ─────────────────────────────────────────
export default function Compare() {
  const [playerA, setPlayerA] = useState(null)
  const [playerB, setPlayerB] = useState(null)
  const [result,  setResult]  = useState(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState(null)

  const canCompare = playerA && playerB && playerA.short_name !== playerB.short_name

  const handleCompare = async () => {
    if (!canCompare) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const data = await comparePlayers(playerA.short_name, playerB.short_name)
      setResult(data)
    } catch (e) {
      setError(e?.response?.data?.detail || 'Erreur lors de la comparaison.')
    } finally {
      setLoading(false)
    }
  }

  // Relancer automatiquement si les deux joueurs changent après un résultat
  const handleSelectA = (p) => { setPlayerA(p); setResult(null); setError(null) }
  const handleSelectB = (p) => { setPlayerB(p); setResult(null); setError(null) }

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">

      {/* HEADER */}
      <div className="mb-12">
        <div className="font-mono text-xs tracking-widest uppercase text-accent mb-4">
          / Comparaison
        </div>
        <h1 className="font-display text-5xl md:text-7xl tracking-tight">
          Face à <span className="text-accent">face</span>
        </h1>
        <p className="mt-6 text-ink/70 max-w-2xl">
          Sélectionnez deux joueurs pour comparer leurs profils et déterminer
          lequel correspond le mieux au vecteur PFA.
        </p>
      </div>

      {/* SÉLECTION */}
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <PlayerSearch
          label="Joueur A"
          color="accent"
          selected={playerA}
          onSelect={handleSelectA}
          exclude={playerB?.short_name}
        />
        <PlayerSearch
          label="Joueur B"
          color="forest"
          selected={playerB}
          onSelect={handleSelectB}
          exclude={playerA?.short_name}
        />
      </div>

      {/* BOUTON COMPARER */}
      <div className="flex items-center gap-4 mb-12">
        <button
          onClick={handleCompare}
          disabled={!canCompare || loading}
          className="flex items-center gap-3 px-8 py-4 bg-ink text-cream text-sm uppercase tracking-widest font-medium hover:bg-accent transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {loading
            ? <span className="w-4 h-4 border-2 border-cream/30 border-t-cream rounded-full animate-spin" />
            : <ArrowRight className="w-4 h-4" />
          }
          {loading ? 'Analyse en cours...' : 'Comparer'}
        </button>
        {!canCompare && playerA && playerB && (
          <span className="text-sm text-accent font-mono">
            Choisissez deux joueurs différents.
          </span>
        )}
      </div>

      {/* ERREUR */}
      {error && (
        <div className="border-2 border-accent p-6 bg-accent/5 mb-10">
          <div className="font-mono text-xs uppercase tracking-widest text-accent mb-1">Erreur</div>
          <div className="text-ink/80">{error}</div>
        </div>
      )}

      {/* RÉSULTATS */}
      <AnimatePresence mode="wait">
        {result && (
          <motion.div
            key={`${result.player_a.short_name}-${result.player_b.short_name}`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="space-y-12"
          >
            <RadarSection result={result} />
            <StatsTable result={result} />
            <Conclusion result={result} />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─────────────────────────────────────────
// Autocomplete joueur
// ─────────────────────────────────────────
function PlayerSearch({ label, color, selected, onSelect, exclude }) {
  const [query,   setQuery]   = useState('')
  const [results, setResults] = useState([])
  const [open,    setOpen]    = useState(false)
  const [busy,    setBusy]    = useState(false)
  const ref      = useRef(null)
  const timerRef = useRef(null)

  const BORDER = color === 'accent' ? 'focus:border-accent' : 'focus:border-forest'
  const BADGE  = color === 'accent'
    ? 'bg-accent/10 text-accent border border-accent/20'
    : 'bg-forest/10 text-forest border border-forest/20'

  // Fermeture sur clic extérieur
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  // Sync query avec la sélection
  useEffect(() => {
    if (selected) setQuery(selected.short_name)
    else setQuery('')
  }, [selected])

  const handleInput = useCallback((val) => {
    setQuery(val)
    onSelect(null)
    clearTimeout(timerRef.current)
    if (val.trim().length < 2) { setResults([]); setOpen(false); return }
    timerRef.current = setTimeout(async () => {
      setBusy(true)
      try {
        const data = await searchPlayers(val.trim(), 8)
        setResults(data.filter(p => p.short_name !== exclude))
        setOpen(true)
      } catch { setResults([]) }
      finally { setBusy(false) }
    }, 300)
  }, [exclude, onSelect])

  const pick = (player) => {
    onSelect(player)
    setQuery(player.short_name)
    setOpen(false)
    setResults([])
  }

  const clear = () => { onSelect(null); setQuery(''); setResults([]); setOpen(false) }

  return (
    <div ref={ref}>
      <div className="text-[10px] uppercase tracking-widest text-ink/60 font-medium mb-2">
        {label}
      </div>

      {/* Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-ink/30 pointer-events-none" />
        <input
          type="text"
          value={query}
          onChange={e => handleInput(e.target.value)}
          placeholder="Rechercher un joueur..."
          className={`w-full bg-white border border-ink/20 pl-10 pr-10 py-3 focus:outline-none transition ${BORDER}`}
        />
        {busy && (
          <Loader className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 animate-spin text-ink/40" />
        )}
        {!busy && query && (
          <button
            onClick={clear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/30 hover:text-ink transition"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Joueur sélectionné */}
      {selected && (
        <div className={`mt-2 px-3 py-2 text-xs font-mono border flex items-center gap-2 ${BADGE}`}>
          <span className="font-medium">{selected.short_name}</span>
          <span className="text-ink/50">·</span>
          <span>{selected.poste}</span>
          <span className="text-ink/50">·</span>
          <span className="truncate">{selected.club}</span>
          <span className="ml-auto font-display text-sm">{selected.overall}</span>
        </div>
      )}

      {/* Dropdown */}
      <AnimatePresence>
        {open && results.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="absolute z-30 bg-white border border-ink/10 shadow-xl w-full max-h-64 overflow-y-auto"
            style={{ width: ref.current?.offsetWidth }}
          >
            {results.map(p => (
              <button
                key={p.short_name}
                onClick={() => pick(p)}
                className="w-full flex items-center justify-between px-4 py-3 hover:bg-cream/60 transition-colors text-left border-b border-ink/5 last:border-0"
              >
                <div>
                  <div className="font-medium text-sm">{p.short_name}</div>
                  <div className="text-xs text-ink/50 truncate">{p.club} · {p.nationality}</div>
                </div>
                <div className="flex items-center gap-3 ml-4 shrink-0">
                  <span className="bg-ink text-cream text-[9px] px-1.5 py-0.5">{p.poste}</span>
                  <span className="font-display text-lg leading-none">{p.overall}</span>
                </div>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ─────────────────────────────────────────
// Radar chart
// ─────────────────────────────────────────
const COLORS = { a: '#c8102e', b: '#1a4d2e', pfa: '#0a0a0a' }

function RadarSection({ result }) {
  const { player_a, player_b, radar } = result
  return (
    <section>
      <div className="font-mono text-[10px] tracking-widest uppercase text-ink/60 mb-3">
        / Radar comparatif
      </div>
      <div className="bg-white border border-ink/10 p-6">
        {/* Légende manuelle */}
        <div className="flex flex-wrap gap-6 mb-4">
          <LegendDot color={COLORS.a} label={player_a.short_name} />
          <LegendDot color={COLORS.b} label={player_b.short_name} />
          <LegendDot color={COLORS.pfa} label="Profil PFA" dashed />
        </div>
        <ResponsiveContainer width="100%" height={480}>
          <RadarChart data={radar} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
            <PolarGrid stroke="#0a0a0a15" />
            <PolarAngleAxis
              dataKey="label"
              tick={{ fontSize: 10, fill: '#0a0a0a', fontFamily: 'JetBrains Mono' }}
            />
            <PolarRadiusAxis angle={90} domain={[0, 1]} tick={{ fontSize: 9 }} tickCount={5} />
            <Radar
              name={player_a.short_name}
              dataKey="player_a"
              stroke={COLORS.a}
              fill={COLORS.a}
              fillOpacity={0.15}
              strokeWidth={2}
            />
            <Radar
              name={player_b.short_name}
              dataKey="player_b"
              stroke={COLORS.b}
              fill={COLORS.b}
              fillOpacity={0.15}
              strokeWidth={2}
            />
            <Radar
              name="PFA"
              dataKey="pfa"
              stroke={COLORS.pfa}
              fill="none"
              strokeWidth={1.5}
              strokeDasharray="5 3"
              strokeOpacity={0.35}
            />
            <Tooltip
              formatter={(val, name) => [val.toFixed(3), name]}
              contentStyle={{ fontSize: 11, fontFamily: 'JetBrains Mono' }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </section>
  )
}

function LegendDot({ color, label, dashed }) {
  return (
    <div className="flex items-center gap-2">
      <svg width="24" height="10">
        <line
          x1="0" y1="5" x2="24" y2="5"
          stroke={color}
          strokeWidth={dashed ? 1.5 : 2}
          strokeDasharray={dashed ? '5 3' : undefined}
          opacity={dashed ? 0.5 : 1}
        />
      </svg>
      <span className="font-mono text-[10px] uppercase tracking-wide text-ink/70">{label}</span>
    </div>
  )
}

// ─────────────────────────────────────────
// Tableau comparatif side-by-side
// ─────────────────────────────────────────
function StatsTable({ result }) {
  const { player_a, player_b, radar } = result

  const LABELS_FR = {
    GKP: 'Gardien', DEF: 'Défenseur', MIL: 'Milieu', ATT: 'Attaquant',
  }

  return (
    <section>
      <div className="font-mono text-[10px] tracking-widest uppercase text-ink/60 mb-3">
        / Tableau comparatif
      </div>

      {/* Entêtes joueurs */}
      <div className="grid grid-cols-3 gap-px bg-ink/10 mb-px">
        <PlayerCard player={player_a} color={COLORS.a} labelFr={LABELS_FR} />
        <div className="bg-ink text-cream flex flex-col items-center justify-center py-6 gap-2">
          <div className="font-mono text-[9px] tracking-widest uppercase text-cream/50">vs</div>
          <div className="font-display text-4xl text-accent">PFA</div>
          <div className="font-mono text-[9px] tracking-widest uppercase text-cream/50">Référence</div>
        </div>
        <PlayerCard player={player_b} color={COLORS.b} labelFr={LABELS_FR} />
      </div>

      {/* Lignes de stats */}
      <div className="border border-ink/10">
        {radar.map((row, i) => {
          const aWins = row.player_a >= row.player_b
          return (
            <div
              key={row.feature}
              className={`grid grid-cols-3 gap-px ${i % 2 === 0 ? 'bg-ink/[0.02]' : 'bg-white'}`}
            >
              {/* Joueur A */}
              <div className={`p-3 flex items-center gap-3 ${aWins ? 'bg-accent/5' : ''}`}>
                <div className="flex-1">
                  <div className="h-1.5 bg-ink/10 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${row.player_a * 100}%`, background: COLORS.a }}
                    />
                  </div>
                </div>
                <span className={`font-mono text-xs w-12 text-right ${aWins ? 'font-bold text-accent' : 'text-ink/60'}`}>
                  {row.player_a.toFixed(3)}
                </span>
              </div>

              {/* PFA */}
              <div className="p-3 flex flex-col items-center justify-center bg-ink/5">
                <span className="font-mono text-[9px] text-ink/40 uppercase tracking-widest truncate w-full text-center">
                  {row.label}
                </span>
                <span className="font-mono text-xs text-ink/60 mt-1">{row.pfa.toFixed(3)}</span>
              </div>

              {/* Joueur B */}
              <div className={`p-3 flex items-center gap-3 flex-row-reverse ${!aWins ? 'bg-forest/5' : ''}`}>
                <div className="flex-1">
                  <div className="h-1.5 bg-ink/10 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${row.player_b * 100}%`, background: COLORS.b }}
                    />
                  </div>
                </div>
                <span className={`font-mono text-xs w-12 text-left ${!aWins ? 'font-bold' : 'text-ink/60'}`}
                  style={!aWins ? { color: COLORS.b } : {}}>
                  {row.player_b.toFixed(3)}
                </span>
              </div>
            </div>
          )
        })}

        {/* Score PFA total */}
        <div className="grid grid-cols-3 gap-px border-t-2 border-ink/20">
          <div className="p-4 bg-accent/10 flex items-center justify-end">
            <span className="font-display text-3xl text-accent">{player_a.pfa_score.toFixed(4)}</span>
          </div>
          <div className="p-4 bg-ink flex items-center justify-center">
            <span className="font-mono text-[9px] text-cream/50 uppercase tracking-widest">Score PFA</span>
          </div>
          <div className="p-4 bg-forest/10 flex items-center">
            <span className="font-display text-3xl" style={{ color: COLORS.b }}>
              {player_b.pfa_score.toFixed(4)}
            </span>
          </div>
        </div>
      </div>

      {/* Points forts / faibles */}
      <div className="grid md:grid-cols-2 gap-px bg-ink/10 mt-px">
        <StrengthsWeaknesses player={player_a} color={COLORS.a} />
        <StrengthsWeaknesses player={player_b} color={COLORS.b} />
      </div>
    </section>
  )
}

function PlayerCard({ player, color, labelFr }) {
  return (
    <div className="bg-cream p-6 flex flex-col gap-1">
      <div className="font-display text-2xl leading-tight">{player.short_name}</div>
      <div className="text-xs text-ink/60 truncate">{player.club}</div>
      <div className="flex items-center gap-2 mt-2">
        <span className="text-[9px] uppercase tracking-widest bg-ink text-cream px-2 py-0.5">
          {labelFr[player.poste] || player.poste}
        </span>
        <span className="font-mono text-xs text-ink/50">{player.nationality}</span>
      </div>
      <div className="mt-3 font-display text-4xl leading-none" style={{ color }}>
        {player.overall}
      </div>
      <div className="text-[9px] uppercase tracking-widest text-ink/50">Note FIFA</div>
    </div>
  )
}

function StrengthsWeaknesses({ player, color }) {
  return (
    <div className="bg-white p-6 space-y-4">
      <div>
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="w-3.5 h-3.5" style={{ color }} />
          <span className="font-mono text-[9px] uppercase tracking-widest text-ink/50">Points forts</span>
        </div>
        <div className="flex flex-wrap gap-1">
          {player.strengths.map(s => (
            <span key={s} className="text-[10px] px-2 py-0.5 border font-mono"
              style={{ borderColor: color, color }}>
              {s}
            </span>
          ))}
        </div>
      </div>
      <div>
        <div className="flex items-center gap-2 mb-2">
          <TrendingDown className="w-3.5 h-3.5 text-ink/40" />
          <span className="font-mono text-[9px] uppercase tracking-widest text-ink/50">Points faibles</span>
        </div>
        <div className="flex flex-wrap gap-1">
          {player.weaknesses.map(w => (
            <span key={w} className="text-[10px] px-2 py-0.5 border border-ink/20 text-ink/50 font-mono">
              {w}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────
// Conclusion automatique
// ─────────────────────────────────────────
function Conclusion({ result }) {
  const { winner, winner_name, player_a, player_b } = result
  const isTie   = winner === 'tie'
  const winData = winner === 'player_a' ? player_a : player_b
  const loseData = winner === 'player_a' ? player_b : player_a
  const diff    = Math.abs(player_a.pfa_score - player_b.pfa_score)

  return (
    <section>
      <div className="font-mono text-[10px] tracking-widest uppercase text-ink/60 mb-3">
        / Conclusion
      </div>
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="bg-ink text-cream p-8 lg:p-12"
      >
        <div className="flex items-start gap-6">
          <div className="w-12 h-12 bg-accent/20 flex items-center justify-center shrink-0">
            <Trophy className="w-6 h-6 text-accent" />
          </div>
          <div>
            {isTie ? (
              <>
                <div className="font-mono text-xs uppercase tracking-widest text-cream/50 mb-2">
                  Résultat
                </div>
                <h2 className="font-display text-4xl md:text-5xl mb-4">
                  Égalité parfaite
                </h2>
                <p className="text-cream/60 max-w-xl">
                  Les deux joueurs ont un score PFA identique ({player_a.pfa_score.toFixed(4)}).
                  Ils correspondent de manière équivalente au vecteur PFA.
                </p>
              </>
            ) : (
              <>
                <div className="font-mono text-xs uppercase tracking-widest text-cream/50 mb-2">
                  Meilleure correspondance au PFA
                </div>
                <h2 className="font-display text-4xl md:text-5xl mb-4">
                  <span className="text-accent">{winner_name}</span>{' '}
                  correspond mieux au PFA
                </h2>
                <div className="grid sm:grid-cols-3 gap-6 mt-6">
                  <Stat label="Score du vainqueur" value={winData.pfa_score.toFixed(4)} accent />
                  <Stat label="Score de l'adversaire" value={loseData.pfa_score.toFixed(4)} />
                  <Stat label="Écart" value={`+${diff.toFixed(4)}`} accent />
                </div>
              </>
            )}
          </div>
        </div>
      </motion.div>
    </section>
  )
}

function Stat({ label, value, accent }) {
  return (
    <div>
      <div className="font-display text-3xl leading-none" style={accent ? { color: '#c8102e' } : {}}>
        {value}
      </div>
      <div className="font-mono text-[9px] uppercase tracking-widest text-cream/40 mt-1">{label}</div>
    </div>
  )
}
