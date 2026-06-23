import axios from 'axios'

const API = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
})

// Ajoute le token JWT à chaque requête
API.interceptors.request.use(config => {
  const token = localStorage.getItem('pfa_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Redirige vers /login si le token est expiré ou invalide
API.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      localStorage.removeItem('pfa_token')
      localStorage.removeItem('pfa_user')
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ─────────────────────────────────────────
// COMPOSITION
// ─────────────────────────────────────────
export const getComposition = (nation = null, formation = '4-3-3') => {
  const params = { formation }
  if (nation) params.nation = nation
  return API.get('/composition', { params }).then(r => r.data)
}

export const getTopPlayers = (nation = null) => {
  const params = nation ? { nation } : {}
  return API.get('/top-players', { params }).then(r => r.data)
}

// ─────────────────────────────────────────
// NATIONS
// ─────────────────────────────────────────
export const getNationsList = (minPlayers = 11) =>
  API.get('/nations-list', { params: { min_players: minPlayers } }).then(r => r.data)

export const getNations = (top = 20) =>
  API.get('/nations', { params: { top } }).then(r => r.data)

export const getAfricanNations = () =>
  API.get('/nations/africa').then(r => r.data)

// ─────────────────────────────────────────
// JOUEURS
// ─────────────────────────────────────────
export const getPlayers = ({ nation, poste, minPfa, limit } = {}) => {
  const params = {}
  if (nation) params.nation = nation
  if (poste) params.poste = poste
  if (minPfa) params.min_pfa = minPfa
  if (limit) params.limit = limit
  return API.get('/players', { params }).then(r => r.data)
}

export const getPlayerByName = (name) =>
  API.get(`/players/${name}`).then(r => r.data)

export const searchPlayers = (q, limit = 10) =>
  API.get('/players/search', { params: { q, limit } }).then(r => r.data)

export const comparePlayers = (playerA, playerB) =>
  API.get('/compare', { params: { player_a: playerA, player_b: playerB } }).then(r => r.data)

// ─────────────────────────────────────────
// PFA & STATS
// ─────────────────────────────────────────
export const getEditorDefaultVector = () =>
  API.get('/editor/default-vector').then(r => r.data)

export const postEditorComposition = (vector, nation, formation) =>
  API.post('/editor/composition', { vector, nation: nation || null, formation }).then(r => r.data)

export const getGraph = (nation = null, formation = '4-3-3') => {
  const params = { formation }
  if (nation) params.nation = nation
  return API.get('/graph', { params }).then(r => r.data)
}

export const getPfaVector = () =>
  API.get('/pfa-vector').then(r => r.data)

export const getStats = () =>
  API.get('/stats').then(r => r.data)

export const getEvaluation = () =>
  API.get('/evaluation').then(r => r.data)

// ─────────────────────────────────────────
// AUTHENTIFICATION
// ─────────────────────────────────────────
export const registerUser = (data) =>
  API.post('/auth/register', data).then(r => r.data)

export const loginUser = (data) =>
  API.post('/auth/login', data).then(r => r.data)

export const getMe = () =>
  API.get('/auth/me').then(r => r.data)

export default API
