# ===============================
#  Stage 1 : Build dependencies
# ===============================
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Mise à jour sécurité
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Copier dépendances Python du service
COPY auth/requirements.txt ./requirements.txt

# Installer dépendances globalement (évite le --user)
RUN pip install --no-cache-dir -r requirements.txt

# ===============================
#  Stage 2 : Runtime
# ===============================
FROM python:3.11-slim-bookworm AS runtime
WORKDIR /app

# Mise à jour sécurité
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root (sécurité)
RUN useradd -m appuser
USER appuser

# Copier dépendances Python globales depuis le builder
COPY --from=builder /usr/local /usr/local

# Copier le code du service
COPY auth /app

# Copier le code commun
COPY common /app/common

# Config Python pour trouver le dossier commun
ENV PYTHONPATH=/app

# Démarrage dynamique : APP_PORT est défini dans docker-compose
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${APP_PORT} --reload"]