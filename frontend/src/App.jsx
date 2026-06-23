import { Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Composition from './pages/Composition'
import Players from './pages/Players'
import PFAVector from './pages/PFAVector'
import GraphExplorer from './pages/GraphExplorer'
import Stats from './pages/Stats'
import Compare from './pages/Compare'
import Login from './pages/Login'
import Register from './pages/Register'

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen flex flex-col relative z-10">
        <Navbar />
        <main className="flex-1">
          <Routes>
            {/* Pages publiques */}
            <Route path="/"         element={<Home />} />
            <Route path="/stats"    element={<Stats />} />
            <Route path="/login"    element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Pages protégées */}
            <Route path="/composition" element={
              <ProtectedRoute><Composition /></ProtectedRoute>
            } />
            <Route path="/players" element={
              <ProtectedRoute><Players /></ProtectedRoute>
            } />
            <Route path="/pfa" element={
              <ProtectedRoute><PFAVector /></ProtectedRoute>
            } />
            <Route path="/compare" element={
              <ProtectedRoute><Compare /></ProtectedRoute>
            } />
            <Route path="/graph" element={
              <ProtectedRoute><GraphExplorer /></ProtectedRoute>
            } />
          </Routes>
        </main>
        <footer className="border-t border-ink/10 py-8 text-center text-xs tracking-widest uppercase text-ink/60">
          <p>PFA GNN — Sélection Optimale par Graph Neural Networks</p>
          <p className="mt-2 font-mono text-[10px]">v2.0.0 · 2026</p>
        </footer>
      </div>
    </AuthProvider>
  )
}

export default App
