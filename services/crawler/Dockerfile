FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir httpx==0.27.2

COPY services/crawler /app/services/crawler
RUN touch /app/services/__init__.py

# Defaults — override via Cloud Run Jobs execution args.
ENV AEGIS_API_BASE=http://aegis-api/
CMD ["python", "-m", "services.crawler.crawler", "--seeds", "/app/services/crawler/seeds.example.json"]
