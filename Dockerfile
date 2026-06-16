# ── ÉTAPE 1 : Builder ──────────────────────────────────
FROM python:3.11-slim AS builder

LABEL org.opencontainers.image.title="healthAI-service-nutrition"
LABEL org.opencontainers.image.description="Service de nutrition pour le projet healthAI"
LABEL org.opencontainers.image.vendor="MSPR Team"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/TEAM-MSPR-EPSI/healthAI-service-nutrition"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.created="2026-06-16T12:00:00+02:00"

WORKDIR /app

# build-essential pour compiler certains packages C
# Il restera UNIQUEMENT dans cette étape, pas dans l'image finale
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# PyTorch CPU-only + requirements installés dans /install
RUN pip install --no-cache-dir --prefix=/install torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── ÉTAPE 2 : Runner (image finale légère) ─────────────
FROM python:3.11-slim AS runner

LABEL org.opencontainers.image.title="healthAI-service-nutrition"
LABEL org.opencontainers.image.description="Service de nutrition pour le projet healthAI"
LABEL org.opencontainers.image.vendor="MSPR Team"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.source="https://github.com/TEAM-MSPR-EPSI/healthAI-service-nutrition"
LABEL org.opencontainers.image.version="1.0.0"
LABEL org.opencontainers.image.created="2026-06-16T12:00:00+02:00"

WORKDIR /app

# curl uniquement pour le healthcheck (build-essential absent ici)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie uniquement les packages installés depuis le builder
COPY --from=builder /install /usr/local

COPY . .

EXPOSE 8001

# --reload retiré : inutile en dehors du dev local
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
