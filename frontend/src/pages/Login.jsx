import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth } from '../context/AuthContext'
import { loginUser } from '../services/api'
import { LogIn, Eye, EyeOff, CheckCircle } from 'lucide-react'

export default function Login() {
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [showPwd,  setShowPwd]  = useState(false)
  const [error,    setError]    = useState(null)
  const [loading,  setLoading]  = useState(false)

  const { login } = useAuth()
  const navigate  = useNavigate()
  const location  = useLocation()
  const from           = location.state?.from?.pathname || '/composition'
  const justRegistered = location.state?.registered === true

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const data = await loginUser({ email, password })
      login(data.access_token, data.user)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err?.response?.data?.detail || 'Erreur de connexion.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        {/* Header */}
        <div className="mb-10">
          <div className="font-mono text-xs tracking-widest uppercase text-accent mb-4">
            / Connexion
          </div>
          <h1 className="font-display text-5xl md:text-6xl tracking-tight">
            Bon retour,<br />
            <span className="text-accent">analyste.</span>
          </h1>
        </div>

        {/* Bannière succès inscription */}
        {justRegistered && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-start gap-3 border-l-4 border-ink bg-ink/5 px-4 py-3 mb-8"
          >
            <CheckCircle className="w-4 h-4 text-ink mt-0.5 shrink-0" />
            <p className="text-sm text-ink/80">
              Compte créé avec succès. Veuillez vous connecter.
            </p>
          </motion.div>
        )}

        {/* Formulaire */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <Field label="Email">
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              autoComplete="email"
              placeholder="vous@exemple.com"
              className="w-full bg-white border border-ink/20 px-4 py-3 focus:border-accent focus:outline-none transition"
            />
          </Field>

          <Field label="Mot de passe">
            <div className="relative">
              <input
                type={showPwd ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder="••••••••"
                className="w-full bg-white border border-ink/20 px-4 py-3 pr-11 focus:border-accent focus:outline-none transition"
              />
              <button
                type="button"
                onClick={() => setShowPwd(v => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/40 hover:text-ink transition"
                tabIndex={-1}
              >
                {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </Field>

          {error && (
            <div className="border-l-4 border-accent bg-accent/5 px-4 py-3 text-sm text-ink/80">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-ink text-cream py-4 font-medium uppercase tracking-widest text-sm hover:bg-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-3"
          >
            {loading ? (
              <span className="inline-block w-4 h-4 border-2 border-cream/30 border-t-cream rounded-full animate-spin" />
            ) : (
              <LogIn className="w-4 h-4" />
            )}
            {loading ? 'Connexion...' : 'Se connecter'}
          </button>
        </form>

        <p className="mt-8 text-sm text-ink/60 text-center">
          Pas encore de compte ?{' '}
          <Link to="/register" className="text-accent hover:underline font-medium">
            Créer un compte
          </Link>
        </p>
      </motion.div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="text-[10px] uppercase tracking-widest text-ink/60 font-medium">
        {label}
      </span>
      <div className="mt-2">{children}</div>
    </label>
  )
}
