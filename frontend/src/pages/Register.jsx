import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { registerUser } from '../services/api'
import { UserPlus, Eye, EyeOff } from 'lucide-react'

export default function Register() {
  const [username, setUsername] = useState('')
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [showPwd,  setShowPwd]  = useState(false)
  const [error,    setError]    = useState(null)
  const [loading,  setLoading]  = useState(false)

  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    if (password.length < 6) {
      setError('Le mot de passe doit contenir au moins 6 caractères.')
      return
    }
    setLoading(true)
    try {
      await registerUser({ username, email, password })
      navigate('/login', { replace: true, state: { registered: true } })
    } catch (err) {
      setError(err?.response?.data?.detail || 'Erreur lors de la création du compte.')
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
            / Créer un compte
          </div>
          <h1 className="font-display text-5xl md:text-6xl tracking-tight">
            Rejoindre<br />
            <span className="text-accent">l'équipe.</span>
          </h1>
        </div>

        {/* Formulaire */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <Field label="Nom d'utilisateur">
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
              minLength={3}
              maxLength={30}
              autoComplete="username"
              placeholder="ex: coach_hassan"
              className="w-full bg-white border border-ink/20 px-4 py-3 focus:border-accent focus:outline-none transition"
            />
          </Field>

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

          <Field label="Mot de passe (6 caractères min.)">
            <div className="relative">
              <input
                type={showPwd ? 'text' : 'password'}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete="new-password"
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
              <UserPlus className="w-4 h-4" />
            )}
            {loading ? 'Création...' : 'Créer le compte'}
          </button>
        </form>

        <p className="mt-8 text-sm text-ink/60 text-center">
          Déjà un compte ?{' '}
          <Link to="/login" className="text-accent hover:underline font-medium">
            Se connecter
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
