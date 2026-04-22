#!/usr/bin/env bash
# Aegis — one-shot GCP deploy script.
#
# What it does:
#   1. Enables required APIs on the target project.
#   2. Creates a Vertex AI Vector Search index + endpoint (if missing).
#   3. Creates a Cloud KMS keyring + asymmetric sign key (if missing).
#   4. Builds + deploys the four mock platform services (x, youtube, meta, telegram).
#   5. Builds + deploys the Aegis API, wired to the mocks via env.
#   6. Deploys the crawler as a Cloud Run Job.
#
# What it does not do:
#   - Provision Firebase Auth / Hosting (do that from the Firebase console; the app's
#     credentials are picked up via the default service account).
#   - Seed Firestore — the API writes collections on first POST.
#
# Safe to re-run: every step is idempotent in intent. Re-runs will skip
# already-created resources. Destructive operations (delete / --force) are
# never in this script.

set -euo pipefail

: "${PROJECT_ID:?PROJECT_ID is required}"
: "${REGION:=us-central1}"
: "${BILLING_ACCOUNT:?BILLING_ACCOUNT is required (link billing to the project)}"

echo "==> Using project: $PROJECT_ID · region: $REGION"

gcloud config set project "$PROJECT_ID"

# 1) Enable APIs
REQUIRED_APIS=(
  aiplatform.googleapis.com
  run.googleapis.com
  artifactregistry.googleapis.com
  cloudbuild.googleapis.com
  firestore.googleapis.com
  storage.googleapis.com
  cloudkms.googleapis.com
  pubsub.googleapis.com
  iam.googleapis.com
)
for api in "${REQUIRED_APIS[@]}"; do
  echo "  enabling $api"
  gcloud services enable "$api" --project="$PROJECT_ID" >/dev/null
done

# 2) KMS keyring + key (used to sign the Merkle root)
KEYRING="${AEGIS_KMS_KEYRING:-aegis-kr}"
KEY="${AEGIS_KMS_KEY_NAME:-aegis-anchor-key}"

if ! gcloud kms keyrings describe "$KEYRING" --location="$REGION" >/dev/null 2>&1; then
  echo "==> Creating KMS keyring $KEYRING"
  gcloud kms keyrings create "$KEYRING" --location="$REGION"
fi

if ! gcloud kms keys describe "$KEY" --keyring="$KEYRING" --location="$REGION" >/dev/null 2>&1; then
  echo "==> Creating KMS key $KEY (RSA_SIGN_PSS_2048_SHA256)"
  gcloud kms keys create "$KEY" \
    --keyring="$KEYRING" \
    --location="$REGION" \
    --purpose="asymmetric-signing" \
    --default-algorithm="rsa-sign-pss-2048-sha256"
fi

KEY_VERSION_NAME="projects/${PROJECT_ID}/locations/${REGION}/keyRings/${KEYRING}/cryptoKeys/${KEY}/cryptoKeyVersions/1"

# 3) Mocks — 4 Cloud Run services
MOCK_ENDPOINTS=()
for p in x youtube meta telegram; do
  echo "==> Deploying mock platform: $p"
  gcloud run deploy "aegis-mock-$p" \
    --source "./services/mock_platforms" \
    --region "$REGION" \
    --allow-unauthenticated \
    --set-env-vars "PLATFORM=$p" \
    --quiet \
    --min-instances=0 \
    --cpu=1 --memory=256Mi
  url=$(gcloud run services describe "aegis-mock-$p" --region "$REGION" --format='value(status.url)')
  MOCK_ENDPOINTS+=("MOCK_$(echo "$p" | tr a-z A-Z)_ENDPOINT=${url}/takedown")
done

# 4) Vector Search index (created separately via console is easier in 48h; leave a placeholder)
if [[ -z "${VERTEX_VECTOR_INDEX_ID:-}" ]]; then
  cat <<'WARN'

  [!] VERTEX_VECTOR_INDEX_ID is not set. Create a Vector Search index in the
      console (ScaNN, 1408-dim, cosine), deploy it to an index endpoint, then
      re-export VERTEX_VECTOR_INDEX_ID / VERTEX_VECTOR_ENDPOINT_ID /
      VERTEX_VECTOR_DEPLOYED_INDEX_ID before this script's final step.
      The API will still boot without these but /detect will return matched=false.

WARN
fi

# 5) Aegis API
ENV_VARS=(
  "VERTEX_AI_PROJECT=${PROJECT_ID}"
  "VERTEX_AI_LOCATION=${REGION}"
  "AEGIS_INDEX_MODE=${AEGIS_INDEX_MODE:-GCP}"
  "AEGIS_STORAGE_MODE=${AEGIS_STORAGE_MODE:-GCP}"
  "AEGIS_KMS_MODE=${AEGIS_KMS_MODE:-GCP}"
  "AEGIS_KMS_KEY=${KEY_VERSION_NAME}"
  "AEGIS_ANCHOR_MODE=${AEGIS_ANCHOR_MODE:-EAGER}"
  "${MOCK_ENDPOINTS[@]}"
)

if [[ -n "${VERTEX_VECTOR_INDEX_ID:-}" ]]; then
  ENV_VARS+=(
    "VERTEX_VECTOR_INDEX_ID=${VERTEX_VECTOR_INDEX_ID}"
    "VERTEX_VECTOR_ENDPOINT_ID=${VERTEX_VECTOR_ENDPOINT_ID}"
    "VERTEX_VECTOR_DEPLOYED_INDEX_ID=${VERTEX_VECTOR_DEPLOYED_INDEX_ID}"
  )
fi

echo "==> Deploying aegis-api"
gcloud run deploy aegis-api \
  --source . \
  --region "$REGION" \
  --allow-unauthenticated \
  --min-instances=1 \
  --cpu=1 --memory=1Gi \
  --set-env-vars "$(IFS=,; echo "${ENV_VARS[*]}")" \
  --quiet

API_URL=$(gcloud run services describe aegis-api --region "$REGION" --format='value(status.url)')
echo "  API: $API_URL"

# 6) Crawler — as a Cloud Run Job so we can run on-demand for the demo
echo "==> Deploying crawler job"
gcloud run jobs deploy aegis-crawler \
  --image "gcr.io/${PROJECT_ID}/aegis-crawler:latest" \
  --region "$REGION" \
  --set-env-vars "AEGIS_API_BASE=${API_URL}" \
  --quiet || echo "  (crawler image not yet built; build+push then re-run)"

# 7) Print a summary + copy-paste env for the frontend
cat <<EOF

==> Done.
    API:          $API_URL
    Mocks:        ${MOCK_ENDPOINTS[@]}
    KMS key ver:  $KEY_VERSION_NAME

Frontend .env (copy into frontend/.env.production):
    VITE_AEGIS_API_BASE=${API_URL}

Firebase Hosting deploy (frontend):
    cd frontend && npm run build && firebase deploy --only hosting

EOF
