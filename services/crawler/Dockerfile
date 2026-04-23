# gcloud run jobs deploy --source ./services/crawler sets the build context
# TO this directory, so COPY paths are relative to services/crawler/.

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir httpx==0.27.2

# Copy crawler source. No cross-repo deps.
COPY . /app/

# Defaults — Cloud Run Jobs exec args can override --args.
ENV AEGIS_API_BASE=http://aegis-api/
CMD ["python", "crawler.py", "--seeds", "/app/seeds.example.json"]
