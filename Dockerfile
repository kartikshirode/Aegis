# Aegis API — the Cloud Run entry point for `gcloud run deploy --source .`.
#
# Build context is the repo root (see .gcloudignore for exclusions). COPY
# paths below are relative to the repo root — backend/, services/, etc.
#
# Local dev can also run `docker build -t aegis-api .` from the repo root.

FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# backend.takedown imports from services.agents — copy both packages.
# services/mock_platforms and services/crawler are harmless dead weight in
# the API image (~50KB); excluding them is not worth a separate pass.
COPY backend  /app/backend
COPY services /app/services

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
