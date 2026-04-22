FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi==0.115.0 uvicorn[standard]==0.32.0 pydantic==2.9.2

COPY services/mock_platforms /app/services/mock_platforms
# Minimal stub so `from services.mock_platforms import ...` resolves
RUN touch /app/services/__init__.py

ENV PLATFORM=mock
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn services.mock_platforms.app:app --host 0.0.0.0 --port ${PORT}"]
