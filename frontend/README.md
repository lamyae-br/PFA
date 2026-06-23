# Frontend React — PFA GNN

Interface utilisateur React + Vite + Tailwind CSS pour le projet de sélection nationale par GNN.

## 📁 Structure

```
frontend/
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.jsx              ← entrée React
    ├── App.jsx               ← routes
    ├── index.css             ← Tailwind + styles globaux
    ├── components/
    │   └── Navbar.jsx
    ├── pages/
    │   ├── Home.jsx          ← page d'accueil
    │   ├── Composition.jsx   ← composition + terrain SVG
    │   ├── Players.jsx       ← explorateur joueurs
    │   ├── PFAVector.jsx     ← radar PFA
    │   └── Stats.jsx         ← stats + évaluation
    └── services/
        └── api.js            ← appels axios
```

## 🚀 Installation

**Prérequis** : Node.js 18+ installé

```bash
cd frontend
npm install
```

## ▶️ Lancement

**1. Lance d'abord le backend** dans un autre terminal :
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**2. Puis lance le frontend** :
```bash
cd frontend
npm run dev
```

Frontend disponible sur : **http://localhost:5173**

## 🎨 Stack

- **React 18** — UI
- **Vite** — bundler ultra-rapide
- **React Router** — navigation
- **Tailwind CSS** — styles
- **Framer Motion** — animations
- **Recharts** — graphiques
- **Lucide React** — icônes
- **Axios** — appels API

## 🎯 Fonctionnalités

| Page | Fonctionnalité |
|---|---|
| **Accueil** | Présentation + KPIs en direct |
| **Composition** | Sélection nation/formation + terrain SVG interactif |
| **Joueurs** | Explorateur filtrable de tous les joueurs |
| **PFA** | Visualisation radar du vecteur PFA |
| **Stats** | Performance GNN + comparaison baselines |

## 🌐 Configuration API

Le frontend appelle `http://localhost:8000/api/...`
Modifier dans `src/services/api.js` si besoin.

CORS est activé côté backend pour tous les domaines.
