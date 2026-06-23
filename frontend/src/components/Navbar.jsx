import { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { LogOut, User, X } from 'lucide-react'

const NAV_LINKS = [
  { to: '/',      label: 'Accueil',      end: true  },
  { to: '/stats', label: 'Statistiques', end: false },
]

const PROTECTED_LINKS = [
  { to: '/composition', label: 'Composition' },
  { to: '/players',     label: 'Joueurs'     },
  { to: '/compare',     label: 'Comparer'    },
  { to: '/graph',       label: 'Graphe'      },
  { to: '/pfa',         label: 'Vecteur PFA' },
]

export default function Navbar() {
  const { isAuthenticated, user, logout } = useAuth()
  const navigate = useNavigate()
  const [showConfirm, setShowConfirm] = useState(false)

  const handleLogoutConfirm = () => {
    setShowConfirm(false)
    logout()
    navigate('/')
  }

  return (
    <>
      <header className="sticky top-0 z-50 bg-cream/80 backdrop-blur-md border-b border-ink/10">
        <nav className="max-w-7xl mx-auto px-6 lg:px-12 py-5 flex items-center justify-between">

          {/* Logo */}
          <NavLink to="/" className="flex items-center gap-3">
            <div className="w-9 h-9 bg-ink text-cream flex items-center justify-center font-display text-xl rounded-sm">
              P
            </div>
            <div>
              <div className="font-display text-xl tracking-wider leading-none">PFA GNN</div>
              <div className="font-mono text-[9px] tracking-widest uppercase text-ink/60 mt-0.5">
                Selection · IA
              </div>
            </div>
          </NavLink>

          {/* Navigation */}
          <ul className="hidden md:flex items-center gap-1">
            {NAV_LINKS.map(link => (
              <li key={link.to}>
                <NavLink
                  to={link.to}
                  end={link.end}
                  className={({ isActive }) =>
                    `nav-link ${isActive ? 'active text-accent' : 'text-ink/70 hover:text-ink'}`
                  }
                >
                  {link.label}
                </NavLink>
              </li>
            ))}

            {isAuthenticated && PROTECTED_LINKS.map(link => (
              <li key={link.to}>
                <NavLink
                  to={link.to}
                  className={({ isActive }) =>
                    `nav-link ${isActive ? 'active text-accent' : 'text-ink/70 hover:text-ink'}`
                  }
                >
                  {link.label}
                </NavLink>
              </li>
            ))}
          </ul>

          {/* Zone utilisateur */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <div className="hidden md:flex items-center gap-2 text-sm text-ink/70">
                  <User className="w-4 h-4 text-accent" />
                  <span className="font-medium text-ink">{user?.username}</span>
                </div>
                <button
                  onClick={() => setShowConfirm(true)}
                  className="flex items-center gap-2 px-3 py-2 border border-ink/20 text-xs uppercase tracking-widest hover:border-accent hover:text-accent transition-colors"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span className="hidden sm:inline">Déconnexion</span>
                </button>
              </>
            ) : (
              <div className="flex items-center gap-2">
                <NavLink
                  to="/login"
                  className="px-4 py-2 text-xs uppercase tracking-widest text-ink/70 hover:text-ink transition-colors"
                >
                  Connexion
                </NavLink>
                <NavLink
                  to="/register"
                  className="px-4 py-2 bg-accent text-cream text-xs uppercase tracking-widest hover:bg-ink transition-colors"
                >
                  S'inscrire
                </NavLink>
              </div>
            )}
          </div>

        </nav>
      </header>

      {/* Modal de confirmation de déconnexion */}
      <AnimatePresence>
        {showConfirm && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-[100] flex items-center justify-center px-6"
            onClick={() => setShowConfirm(false)}
          >
            {/* Fond sombre */}
            <div className="absolute inset-0 bg-ink/60 backdrop-blur-sm" />

            {/* Carte */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 12 }}
              transition={{ duration: 0.2 }}
              className="relative bg-cream w-full max-w-sm shadow-2xl"
              onClick={e => e.stopPropagation()}
            >
              {/* Fermer */}
              <button
                onClick={() => setShowConfirm(false)}
                className="absolute top-4 right-4 text-ink/40 hover:text-ink transition-colors"
                aria-label="Fermer"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="p-8">
                {/* Icône */}
                <div className="w-10 h-10 bg-accent/10 flex items-center justify-center mb-6">
                  <LogOut className="w-5 h-5 text-accent" />
                </div>

                {/* Texte */}
                <h2 className="font-display text-2xl tracking-tight mb-2">
                  Se déconnecter ?
                </h2>
                <p className="text-sm text-ink/60 mb-8 leading-relaxed">
                  Êtes-vous sûr de vouloir vous déconnecter ?
                  Vous devrez vous reconnecter pour accéder aux outils d'analyse.
                </p>

                {/* Actions */}
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowConfirm(false)}
                    className="flex-1 py-3 border border-ink/20 text-xs uppercase tracking-widest hover:border-ink transition-colors"
                  >
                    Annuler
                  </button>
                  <button
                    onClick={handleLogoutConfirm}
                    className="flex-1 py-3 bg-accent text-cream text-xs uppercase tracking-widest hover:bg-ink transition-colors"
                  >
                    Se déconnecter
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
