# gcloud run deploy --source ./services/mock_platforms sets the build context
# TO this directory, so paths in COPY are relative to services/mock_platforms/.

FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
      fastapi==0.115.0 \
      "uvicorn[standard]==0.32.0" \
      pydantic==2.9.2

# Copy the service source (app.py, etc.). No cross-repo deps.
COPY . /app/

ENV PLATFORM=mock
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT}"]
