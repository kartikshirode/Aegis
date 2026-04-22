# Mock platform endpoints

Four FastAPI services that stand in for X / YouTube / Meta / Telegram during the Aegis demo and benchmark. They receive Aegis takedown notices at `POST /takedown` and return a structured receipt shaped like the real platform's response would be.

## What they are

- A benchmark harness for the Aegis takedown pipeline.
- Deterministic: the same `notice_id` always returns the same ticket ID.
- In-memory only. Restart clears the store.
- Honest: the `pipeline integrity` metric in `docs/benchmarks.md` measures **our pipeline's ability to submit a well-formed notice** to these mocks, not the real platforms' response rates.

## What they are not

- Not real platform APIs. Nothing submitted here reaches X / YouTube / Meta / Telegram.
- Not a piracy-facilitation tool. They accept Aegis-authored takedown notices; they do not host candidate content.
- Not part of the product surface exposed to users. They are service-to-service only.

## Run locally

```
# terminal A
PLATFORM=x uvicorn services.mock_platforms.app:app --port 8101

# terminal B
PLATFORM=youtube uvicorn services.mock_platforms.app:app --port 8102

# terminal C
PLATFORM=meta uvicorn services.mock_platforms.app:app --port 8103

# terminal D
PLATFORM=telegram uvicorn services.mock_platforms.app:app --port 8104
```

Then in the Aegis API environment:

```
export MOCK_X_ENDPOINT=http://localhost:8101/takedown
export MOCK_YOUTUBE_ENDPOINT=http://localhost:8102/takedown
export MOCK_META_ENDPOINT=http://localhost:8103/takedown
export MOCK_TELEGRAM_ENDPOINT=http://localhost:8104/takedown
```

## Deploy to Cloud Run

```
for p in x youtube meta telegram; do
  gcloud run deploy aegis-mock-$p \
    --source . \
    --set-env-vars PLATFORM=$p \
    --region us-central1 \
    --allow-unauthenticated
done
```

Each returns a URL. Set the four `MOCK_*_ENDPOINT` vars on the Aegis API Cloud Run revision.

## SLA timings returned

| Platform | Default SLA in receipt |
|---|---|
| x        | 24 hours  |
| youtube  | 72 hours  |
| meta     | 48 hours  |
| telegram | 72 hours  |
| any jurisdiction=IN with synthetic/morphed/Rule 3(2)(b) content | 24 hours (overrides) |

The 24-hour IN-synthetic timeline matches MeitY's November 2023 advisory under the IT Rules 2021.
