# Backend FastAPI + GNN (PyTorch CPU)
FROM python:3.10-slim

WORKDIR /app

# Dépendances système nécessaires à la compilation de certaines libs
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential pkg-config default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# 1) PyTorch CPU + PyTorch Geometric (lourds : installés en premier pour le cache)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir torch_geometric

# 2) Dépendances applicatives
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 3) Code source + données (modèles .pt, CSV, vecteur PFA)
COPY . .

WORKDIR /app/backend
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
