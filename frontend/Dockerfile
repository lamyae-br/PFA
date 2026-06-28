# Frontend React + Vite (serveur de développement)
FROM node:20-slim

WORKDIR /app

# Installe les dépendances (couche cachée tant que package.json ne change pas)
COPY package*.json ./
RUN npm install

# Code source
COPY . .

EXPOSE 5173
# --host 0.0.0.0 pour exposer le serveur Vite hors du conteneur
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
