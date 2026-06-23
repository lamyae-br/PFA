import { useEffect, useState, useRef, useCallback } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { motion, AnimatePresence } from 'framer-motion'
import { getGraph, getNationsList } from '../services/api'
import { Loader, X, Share2, Zap } from 'lucide-react'

const FORMATIONS = ['4-3-3', '4-4-2', '4-2-3-1', '3-5-2', '3-4-3', '5-3-2']

const POSTE_COLOR = {
  GKP: '#d4af37',
  DEF: '#1a4d2e',
  MIL: '#1e40af',
  ATT: '#c8102e',
}

const POSTE_LABEL = {
  GKP: 'Gardien',
  DEF: 'Défenseur',
  MIL: 'Milieu',
  ATT: 'Attaquant',
}

function Select({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block font-mono text-xs tracking-widest uppercase text-ink/50 mb-2">
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
        <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-ink/40">
          ▾
        </div>
      </div>
    </div>
  )
}

function NodePanel({ node, onClose }) {
  if (!node) return null
  const color = POSTE_COLOR[node.poste] || '#555'
  const pct = Math.round(node.pfa_score * 100)

  return (
    <motion.div
      initial={{ opacity: 0, x: 24 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 24 }}
      transition={{ duration: 0.2 }}
      className="absolute top-4 right-4 w-64 bg-cream border border-ink/15 shadow-xl z-10"
    >
      {/* Color band */}
      <div className="h-1 w-full" style={{ background: color }} />

      <div className="p-5">
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="font-mono text-[10px] tracking-widest uppercase mb-1"
               style={{ color }}>
              {POSTE_LABEL[node.poste] || node.poste}
            </p>
            <h3 className="font-display text-xl tracking-tight leading-tight">{node.name}</h3>
          </div>
          <button
            onClick={onClose}
            className="text-ink/30 hover:text-ink transition-colors mt-0.5"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-2 text-sm">
          <Row label="Club" value={node.club} />
          <Row label="Nation" value={node.nationality} />
          <Row label="Note FIFA" value={node.overall} />
        </div>

        {/* PFA score bar */}
        <div className="mt-4">
          <div className="flex justify-between font-mono text-xs text-ink/50 mb-1.5">
            <span>Score PFA</span>
            <span className="text-ink font-semibold">{pct}%</span>
          </div>
          <div className="h-1.5 bg-ink/10 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              className="h-full rounded-full"
              style={{ background: color }}
            />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between items-baseline gap-2">
      <span className="text-ink/50 font-mono text-[11px] uppercase tracking-wider shrink-0">{label}</span>
      <span className="text-ink/90 font-medium text-right truncate">{value}</span>
    </div>
  )
}

export default function GraphExplorer() {
  const [nation, setNation] = useState('Morocco')
  const [formation, setFormation] = useState('4-3-3')
  const [nations, setNations] = useState([])
  const [graphData, setGraphData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [selectedNode, setSelectedNode] = useState(null)
  const graphRef = useRef(null)
  const containerRef = useRef(null)
  const [dims, setDims] = useState({ width: 800, height: 560 })

  // Load nations
  useEffect(() => {
    getNationsList(11).then(d => setNations(d.nations || [])).catch(() => {})
  }, [])

  // Resize observer
  useEffect(() => {
    if (!containerRef.current) return
    const ro = new ResizeObserver(entries => {
      for (const e of entries) {
        setDims({ width: e.contentRect.width, height: Math.max(500, e.contentRect.height) })
      }
    })
    ro.observe(containerRef.current)
    return () => ro.disconnect()
  }, [])

  // Fetch graph
  useEffect(() => {
    setLoading(true)
    setError(null)
    setSelectedNode(null)
    getGraph(nation || null, formation)
      .then(data => {
        // react-force-graph needs "links", not "edges"
        setGraphData({
          nodes: data.nodes.map(n => ({ ...n })),
          links: data.edges.map(e => ({ ...e })),
          stats: data.stats,
          nation: data.nation,
          formation: data.formation,
        })
      })
      .catch(e => setError(e?.response?.data?.detail || 'Erreur lors du chargement du graphe'))
      .finally(() => setLoading(false))
  }, [nation, formation])

  // Auto-zoom once graph is loaded
  useEffect(() => {
    if (graphData && graphRef.current) {
      setTimeout(() => graphRef.current?.zoomToFit(400, 60), 300)
    }
  }, [graphData])

  const handleNodeClick = useCallback(node => {
    setSelectedNode(prev => prev?.id === node.id ? null : node)
  }, [])

  const paintNode = useCallback((node, ctx, globalScale) => {
    const color = POSTE_COLOR[node.poste] || '#888'
    const r = node.id === selectedNode?.id ? 9 : 7

    // Glow for selected
    if (node.id === selectedNode?.id) {
      ctx.beginPath()
      ctx.arc(node.x, node.y, r + 4, 0, 2 * Math.PI)
      ctx.fillStyle = color + '33'
      ctx.fill()
    }

    // Node circle
    ctx.beginPath()
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
    ctx.fillStyle = color
    ctx.fill()

    // White border
    ctx.beginPath()
    ctx.arc(node.x, node.y, r, 0, 2 * Math.PI)
    ctx.strokeStyle = 'rgba(255,255,255,0.6)'
    ctx.lineWidth = 1.5 / globalScale
    ctx.stroke()

    // Label
    const fontSize = Math.max(3.5, 5 / globalScale)
    ctx.font = `${fontSize}px sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.fillStyle = '#111'
    const label = node.name.split(' ').pop() // last name only
    ctx.fillText(label, node.x, node.y + r + 1.5 / globalScale)
  }, [selectedNode])

  const getLinkColor = useCallback(link =>
    link.type === 'graphe' ? 'rgba(200,16,46,0.55)' : 'rgba(100,100,100,0.25)'
  , [])

  const getLinkWidth = useCallback(link =>
    link.type === 'graphe' ? link.weight * 2.5 + 0.5 : 0.8
  , [])

  const getLinkDash = useCallback(link =>
    link.type === 'graphe' ? null : [3, 3]
  , [])

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16">

      {/* HEADER */}
      <div className="mb-10">
        <div className="font-mono text-xs tracking-widest uppercase text-accent mb-4">
          / Graphe GNN
        </div>
        <h1 className="font-display text-5xl md:text-7xl tracking-tight">
          Graph <span className="text-accent">Explorer</span>
        </h1>
        <p className="mt-4 text-ink/70 max-w-2xl">
          Visualisez le sous-graphe GNN des 11 joueurs sélectionnés. Les arêtes rouges
          représentent les connexions du graphe d'entraînement ; les arêtes grises la
          similarité cosinus des embeddings.
        </p>
      </div>

      {/* CONTROLS */}
      <div className="grid md:grid-cols-2 gap-4 mb-8">
        <Select
          label="Nation"
          value={nation}
          onChange={v => { setNation(v); setSelectedNode(null) }}
          options={[
            { value: '', label: '🌍 Monde (toutes nations)' },
            ...nations.map(n => ({ value: n.nation, label: `${n.nation} (${n.players_count})` }))
          ]}
        />
        <Select
          label="Formation"
          value={formation}
          onChange={v => { setFormation(v); setSelectedNode(null) }}
          options={FORMATIONS.map(f => ({ value: f, label: f }))}
        />
      </div>

      {/* STATS BAR */}
      {graphData?.stats && !loading && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-wrap gap-6 mb-6 font-mono text-xs text-ink/60"
        >
          <StatChip icon={<Share2 className="w-3 h-3" />} label="Nœuds" value={graphData.stats.total_nodes} />
          <StatChip icon={<Zap className="w-3 h-3" />} label="Arêtes graphe" value={graphData.stats.graphe_edges} accent />
          <StatChip icon={<Zap className="w-3 h-3 opacity-40" />} label="Similarité" value={graphData.stats.similarite_edges} />
        </motion.div>
      )}

      {/* GRAPH AREA */}
      <div
        ref={containerRef}
        className="relative border border-ink/10 bg-[#fafaf8] overflow-hidden"
        style={{ height: 580 }}
      >
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-cream/80 z-20">
            <Loader className="w-6 h-6 animate-spin text-accent" />
          </div>
        )}

        {error && !loading && (
          <div className="absolute inset-0 flex items-center justify-center z-20">
            <div className="text-center px-8">
              <p className="text-sm text-red-600 font-medium">{error}</p>
            </div>
          </div>
        )}

        {graphData && !loading && !error && (
          <ForceGraph2D
            ref={graphRef}
            graphData={{ nodes: graphData.nodes, links: graphData.links }}
            width={dims.width}
            height={dims.height}
            nodeCanvasObject={paintNode}
            nodeCanvasObjectMode={() => 'replace'}
            nodePointerAreaPaint={(node, color, ctx) => {
              ctx.beginPath()
              ctx.arc(node.x, node.y, 10, 0, 2 * Math.PI)
              ctx.fillStyle = color
              ctx.fill()
            }}
            linkColor={getLinkColor}
            linkWidth={getLinkWidth}
            linkLineDash={getLinkDash}
            linkDirectionalParticles={link => link.type === 'graphe' ? 2 : 0}
            linkDirectionalParticleSpeed={0.005}
            linkDirectionalParticleWidth={1.5}
            linkDirectionalParticleColor={() => 'rgba(200,16,46,0.8)'}
            onNodeClick={handleNodeClick}
            cooldownTicks={120}
            d3AlphaDecay={0.02}
            d3VelocityDecay={0.35}
            backgroundColor="#fafaf8"
          />
        )}

        {/* Node detail panel */}
        <AnimatePresence>
          {selectedNode && (
            <NodePanel node={selectedNode} onClose={() => setSelectedNode(null)} />
          )}
        </AnimatePresence>

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-cream/90 backdrop-blur-sm border border-ink/10 px-4 py-3 text-xs space-y-2">
          <p className="font-mono uppercase tracking-widest text-ink/40 text-[10px] mb-2">Postes</p>
          {Object.entries(POSTE_COLOR).map(([k, c]) => (
            <div key={k} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full shrink-0" style={{ background: c }} />
              <span className="text-ink/70">{POSTE_LABEL[k]}</span>
            </div>
          ))}
          <div className="border-t border-ink/10 pt-2 mt-2 space-y-1.5">
            <div className="flex items-center gap-2">
              <div className="w-6 h-0.5 bg-accent/70 shrink-0" />
              <span className="text-ink/70">Graphe GNN</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-6 h-0 border-t border-dashed border-ink/40 shrink-0" />
              <span className="text-ink/70">Similarité cosinus</span>
            </div>
          </div>
        </div>
      </div>

      {/* Hint */}
      {graphData && !loading && (
        <p className="mt-3 text-center font-mono text-xs text-ink/40">
          Cliquez sur un nœud pour afficher ses informations
        </p>
      )}
    </div>
  )
}

function StatChip({ icon, label, value, accent }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={accent ? 'text-accent' : ''}>{icon}</span>
      <span>{label} :</span>
      <span className={`font-semibold ${accent ? 'text-accent' : 'text-ink'}`}>{value}</span>
    </div>
  )
}
