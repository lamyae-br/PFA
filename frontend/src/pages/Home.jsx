import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { ArrowRight, Network, Target, Users, BarChart3 } from 'lucide-react'
import { getStats } from '../services/api'

export default function Home() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    getStats().then(setStats).catch(() => { /* stats affichées avec valeurs par défaut */ })
  }, [])

  return (
    <div className="max-w-7xl mx-auto px-6 lg:px-12 py-16 lg:py-24">

      {/* HERO */}
      <section className="grid lg:grid-cols-12 gap-12 items-end mb-32">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          className="lg:col-span-8"
        >
          
          <h1 className="font-display text-6xl md:text-8xl lg:text-9xl leading-[0.85] tracking-tight">
            Sélection<br/>
            <span className="text-accent">Optimale</span><br/>
            <span className="text-ink/40">par GNN</span>
          </h1>
          <p className="mt-10 max-w-xl text-lg text-ink/70 leading-relaxed">
            Système d'aide à la décision basé sur les <strong className="text-ink">Graph Neural Networks</strong>{' '}
            pour la sélection d'une composition d'équipe nationale optimale,
            calibrée sur un projet de jeu tactique.
          </p>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link to="/composition" className="btn-primary flex items-center gap-3 group">
              Voir la composition
              <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link to="/stats" className="px-6 py-3 border border-ink/20 text-sm uppercase tracking-wider hover:border-ink transition">
              Performance modèle
            </Link>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="lg:col-span-4 space-y-1"
        >
          <div className="font-mono text-[10px] tracking-widest uppercase text-ink/50 mb-3">
            Métriques clés
          </div>
          <KPI label="R² du modèle" value={stats?.gnn_r2 ? stats.gnn_r2.toFixed(4) : '0.9911'} />
          <KPI label="Joueurs analysés" value={stats?.total_players?.toLocaleString() || '20,993'} />
          <KPI label="Nations couvertes" value={stats?.total_nations || '160+'} />
          <KPI label="Arêtes du graphe" value={stats?.total_edges?.toLocaleString() || '85,932'} />
        </motion.div>
      </section>

      {/* CONCEPT */}
      <section className="mb-32">
        <div className="font-mono text-xs tracking-widest uppercase text-ink/50 mb-6">
          / Le concept
        </div>
        <h2 className="font-display text-4xl md:text-6xl leading-tight max-w-4xl mb-16">
          Modéliser les interactions entre joueurs<br/>
          <span className="text-ink/40">comme un graphe.</span>
        </h2>

        <div className="grid md:grid-cols-3 gap-px bg-ink/10">
          <Feature
            icon={<Network className="w-6 h-6" />}
            title="Graph Neural Network"
            text="GraphSAGE 3 couches qui apprend des passes réelles entre joueurs (StatsBomb)."
          />
          <Feature
            icon={<Target className="w-6 h-6" />}
            title="Vecteur PFA"
            text="18 dimensions tactiques définissant le profil idéal de l'équipe."
          />
          <Feature
            icon={<Users className="w-6 h-6" />}
            title="Multi-nations"
            text="160+ nationalités supportées. Génère un XI pour n'importe quelle équipe."
          />
        </div>
      </section>

      {/* PIPELINE */}
      <section className="mb-32">
        <div className="font-mono text-xs tracking-widest uppercase text-ink/50 mb-6">
          / Pipeline
        </div>
        <div className="grid md:grid-cols-5 gap-4">
          {[
            'Données FIFA + StatsBomb',
            'Construction du graphe',
            'Entraînement GNN',
            'Similarité PFA',
            'Composition optimale'
          ].map((step, i) => (
            <div key={i} className="border-l-2 border-accent pl-4 py-2">
              <div className="font-mono text-[10px] tracking-widest text-accent">
                {String(i + 1).padStart(2, '0')}
              </div>
              <div className="mt-2 text-sm font-medium leading-tight">{step}</div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-ink text-cream py-20 px-8 lg:px-16 -mx-6 lg:-mx-12">
        <div className="max-w-4xl">
          <BarChart3 className="w-12 h-12 text-accent mb-8" />
          <h2 className="font-display text-5xl md:text-7xl leading-none mb-8">
            Prêt à composer<br/>
            <span className="text-accent">votre XI ?</span>
          </h2>
          <p className="text-cream/70 text-lg mb-10 max-w-xl">
            Sélectionnez une nation, choisissez votre formation, et laissez le GNN
            assembler la composition optimale en fonction du projet de jeu.
          </p>
          <Link
            to="/composition"
            className="inline-flex items-center gap-3 bg-accent text-cream px-8 py-4 text-sm uppercase tracking-widest font-medium hover:bg-cream hover:text-ink transition-all"
          >
            Lancer la sélection
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </div>
  )
}

function KPI({ label, value }) {
  return (
    <div className="border-l-2 border-ink/20 hover:border-accent pl-4 py-3 transition-colors">
      <div className="font-display text-3xl leading-none">{value}</div>
      <div className="text-[10px] uppercase tracking-widest text-ink/60 mt-1">{label}</div>
    </div>
  )
}

function Feature({ icon, title, text }) {
  return (
    <div className="bg-cream p-8 hover:bg-white transition-colors">
      <div className="text-accent mb-6">{icon}</div>
      <h3 className="font-display text-2xl tracking-wide mb-3">{title}</h3>
      <p className="text-sm text-ink/70 leading-relaxed">{text}</p>
    </div>
  )
}
