# Aegis — PowerShell one-shot (ish) GCP deploy.
#
# Native Windows version of infra/deploy.sh. Does not need WSL / bash.
# Tested on Windows PowerShell 5.1; also works on PowerShell 7+.
#
# NOTE: Vertex AI Vector Search index creation is NOT automated here.
# Create the index + endpoint in the console first (ScaNN, 1408-dim, cosine),
# then set the three VERTEX_VECTOR_* env vars before running.
#
# Run:
#   $env:PROJECT_ID = "aegis-sc2026-xxxxx"
#   $env:REGION = "us-central1"
#   $env:BILLING_ACCOUNT = "XXXXXX-XXXXXX-XXXXXX"   # gcloud billing accounts list
#   .\infra\deploy.ps1
#
# Safe to re-run: idempotent. KMS keyring/key create is skipped if present.
# Cloud Run services update in place.

# IMPORTANT: do NOT set $ErrorActionPreference = "Stop" at script scope.
# In PS 5.1, combined with `2>&1`, that wraps native-command stderr in an
# ErrorRecord and throws on any `gcloud ... describe` that hits NOT_FOUND —
# which is exactly what the existence-probe pattern relies on catching.

# ---------- helpers ----------

function Invoke-Gcloud {
    <#
      Run gcloud and throw with context on non-zero exit. Stream stdout/stderr
      directly to the console (no 2>&1 merging, to avoid PS-5.1 ErrorRecord wrapping).
    #>
    param([Parameter(ValueFromRemainingArguments = $true)][string[]] $Args)
    & gcloud @Args
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud $($Args -join ' ') failed with exit $LASTEXITCODE"
    }
}

function Test-GcloudResource {
    <#
      Existence probe. Discards stderr so NOT_FOUND doesn't become an ErrorRecord
      under PS 5.1. Returns $true iff the resource exists (exit 0).
    #>
    param([Parameter(ValueFromRemainingArguments = $true)][string[]] $Args)
    & gcloud @Args 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

function Get-GcloudValue {
    <#
      Run gcloud and return trimmed stdout. Throws on non-zero.
    #>
    param([Parameter(ValueFromRemainingArguments = $true)][string[]] $Args)
    $out = & gcloud @Args
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud $($Args -join ' ') failed with exit $LASTEXITCODE"
    }
    return ($out | Out-String).Trim()
}

# ---------- prerequisites ----------

if (-not $env:PROJECT_ID)      { throw "PROJECT_ID env var is required" }
if (-not $env:BILLING_ACCOUNT) { throw "BILLING_ACCOUNT env var is required (find via: gcloud billing accounts list)" }
if (-not $env:REGION)          { $env:REGION = "us-central1" }

if (-not (Get-Command gcloud -ErrorAction SilentlyContinue)) {
    throw "gcloud CLI not found. Install: https://cloud.google.com/sdk/docs/install"
}

Write-Host "==> Using project: $($env:PROJECT_ID)  region: $($env:REGION)" -ForegroundColor Cyan
Invoke-Gcloud config set project $env:PROJECT_ID

# Link billing. Non-fatal if already linked (gcloud exits 0 in that case anyway).
& gcloud billing projects link $env:PROJECT_ID --billing-account=$env:BILLING_ACCOUNT 2>$null | Out-Null

# ---------- 1. enable APIs ----------

$RequiredApis = @(
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "cloudkms.googleapis.com",
    "pubsub.googleapis.com",
    "iam.googleapis.com"
)
foreach ($api in $RequiredApis) {
    Write-Host "  enabling $api"
    Invoke-Gcloud services enable $api --project=$env:PROJECT_ID
}

# ---------- 2. Cloud KMS keyring + key ----------

$Keyring = if ($env:AEGIS_KMS_KEYRING)  { $env:AEGIS_KMS_KEYRING }  else { "aegis-kr" }
$Key     = if ($env:AEGIS_KMS_KEY_NAME) { $env:AEGIS_KMS_KEY_NAME } else { "aegis-anchor-key" }

if (-not (Test-GcloudResource kms keyrings describe $Keyring --location=$env:REGION)) {
    Write-Host "==> Creating KMS keyring $Keyring" -ForegroundColor Cyan
    Invoke-Gcloud kms keyrings create $Keyring --location=$env:REGION
} else {
    Write-Host "    KMS keyring $Keyring already exists"
}

if (-not (Test-GcloudResource kms keys describe $Key --keyring=$Keyring --location=$env:REGION)) {
    Write-Host "==> Creating KMS key $Key (rsa-sign-pss-2048-sha256)" -ForegroundColor Cyan
    Invoke-Gcloud kms keys create $Key `
        --keyring=$Keyring `
        --location=$env:REGION `
        --purpose="asymmetric-signing" `
        --default-algorithm="rsa-sign-pss-2048-sha256"
} else {
    Write-Host "    KMS key $Key already exists"
}

$KeyVersion = "projects/$($env:PROJECT_ID)/locations/$($env:REGION)/keyRings/$Keyring/cryptoKeys/$Key/cryptoKeyVersions/1"

# ---------- 3. four mock platform services ----------

$MockEndpoints = @{}
foreach ($p in @("x", "youtube", "meta", "telegram")) {
    Write-Host "==> Deploying mock platform: $p" -ForegroundColor Cyan
    Invoke-Gcloud run deploy "aegis-mock-$p" `
        --source ./services/mock_platforms `
        --region $env:REGION `
        --allow-unauthenticated `
        --set-env-vars "PLATFORM=$p" `
        --quiet `
        --min-instances=0 `
        --cpu=1 --memory=256Mi

    $url = Get-GcloudValue run services describe "aegis-mock-$p" --region $env:REGION --format='value(status.url)'
    $MockEndpoints[$p] = "$url/takedown"
    Write-Host "  $p : $url/takedown"
}

# ---------- 4. Aegis API ----------

if (-not $env:VERTEX_VECTOR_INDEX_ID) {
    Write-Warning "VERTEX_VECTOR_INDEX_ID not set. Create a Vector Search index + endpoint in the console (ScaNN, 1408-dim, cosine), then re-export VERTEX_VECTOR_INDEX_ID / VERTEX_VECTOR_ENDPOINT_ID / VERTEX_VECTOR_DEPLOYED_INDEX_ID and re-run this script. API will still boot but /detect returns matched=false."
}

$EnvVars = @(
    "VERTEX_AI_PROJECT=$($env:PROJECT_ID)",
    "VERTEX_AI_LOCATION=$($env:REGION)",
    "AEGIS_INDEX_MODE=$(if ($env:AEGIS_INDEX_MODE) { $env:AEGIS_INDEX_MODE } else { 'GCP' })",
    "AEGIS_STORAGE_MODE=$(if ($env:AEGIS_STORAGE_MODE) { $env:AEGIS_STORAGE_MODE } else { 'GCP' })",
    "AEGIS_KMS_MODE=$(if ($env:AEGIS_KMS_MODE) { $env:AEGIS_KMS_MODE } else { 'GCP' })",
    "AEGIS_KMS_KEY=$KeyVersion",
    "AEGIS_ANCHOR_MODE=$(if ($env:AEGIS_ANCHOR_MODE) { $env:AEGIS_ANCHOR_MODE } else { 'EAGER' })",
    "MOCK_X_ENDPOINT=$($MockEndpoints['x'])",
    "MOCK_YOUTUBE_ENDPOINT=$($MockEndpoints['youtube'])",
    "MOCK_META_ENDPOINT=$($MockEndpoints['meta'])",
    "MOCK_TELEGRAM_ENDPOINT=$($MockEndpoints['telegram'])"
)

if ($env:VERTEX_VECTOR_INDEX_ID) {
    $EnvVars += "VERTEX_VECTOR_INDEX_ID=$($env:VERTEX_VECTOR_INDEX_ID)"
    $EnvVars += "VERTEX_VECTOR_ENDPOINT_ID=$($env:VERTEX_VECTOR_ENDPOINT_ID)"
    $EnvVars += "VERTEX_VECTOR_DEPLOYED_INDEX_ID=$($env:VERTEX_VECTOR_DEPLOYED_INDEX_ID)"
}

# Custom "^|^" delimiter so values with "," survive (e.g. URLs with query strings).
$EnvVarsJoined = "^|^" + ($EnvVars -join "|")

Write-Host "==> Deploying aegis-api" -ForegroundColor Cyan
Invoke-Gcloud run deploy aegis-api `
    --source . `
    --region $env:REGION `
    --allow-unauthenticated `
    --min-instances=1 `
    --cpu=1 --memory=1Gi `
    --set-env-vars $EnvVarsJoined `
    --quiet

$ApiUrl = Get-GcloudValue run services describe aegis-api --region $env:REGION --format='value(status.url)'
Write-Host "  API: $ApiUrl" -ForegroundColor Green

# ---------- 5. crawler as Cloud Run Job ----------

Write-Host "==> Deploying crawler job" -ForegroundColor Cyan
Invoke-Gcloud run jobs deploy aegis-crawler `
    --source ./services/crawler `
    --region $env:REGION `
    --set-env-vars "AEGIS_API_BASE=$ApiUrl" `
    --quiet

# ---------- summary ----------

Write-Host ""
Write-Host "==> Done." -ForegroundColor Green
Write-Host "    API:          $ApiUrl"
foreach ($p in @("x", "youtube", "meta", "telegram")) {
    Write-Host "    mock $($p.PadRight(8)): $($MockEndpoints[$p])"
}
Write-Host "    KMS key ver:  $KeyVersion"
Write-Host ""
Write-Host "Frontend .env.production (paste into frontend/.env.production):" -ForegroundColor Yellow
Write-Host "    VITE_AEGIS_API_BASE=$ApiUrl"
Write-Host ""
Write-Host "Verify real-GCP mode before demo:" -ForegroundColor Yellow
Write-Host "    curl $ApiUrl/demo/status"
Write-Host ""
Write-Host "Frontend deploy:" -ForegroundColor Yellow
Write-Host "    cd frontend; npm install; npm run build; firebase deploy --only hosting"
