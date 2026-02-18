# Deploy to Google Cloud Run (PowerShell version)
# Usage: .\deploy-cloudrun.ps1 -ProjectId "your-project" -Region "us-central1"

param(
    [Parameter(Mandatory=$false)]
    [string]$ProjectId = "your-gcp-project",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-central1",
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "constructio-mcp-server"
)

$ErrorActionPreference = "Stop"

$ImageName = "gcr.io/$ProjectId/$ServiceName"

Write-Host "🚀 Deploying $ServiceName to Cloud Run..." -ForegroundColor Green
Write-Host "   Project: $ProjectId"
Write-Host "   Region: $Region"
Write-Host ""

# Check if gcloud is installed
if (!(Get-Command gcloud -ErrorAction SilentlyContinue)) {
    Write-Host "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install" -ForegroundColor Red
    exit 1
}

# Check environment variables
$requiredVars = @("GCS_BUCKET")
foreach ($var in $requiredVars) {
    if (!(Test-Path env:$var)) {
        Write-Host "❌ Required environment variable $var is not set" -ForegroundColor Red
        exit 1
    }
}

# Set project
gcloud config set project $ProjectId

# Build container image
Write-Host "📦 Building container image..." -ForegroundColor Cyan
gcloud builds submit --tag $ImageName

# Deploy to Cloud Run
Write-Host "🚢 Deploying to Cloud Run..." -ForegroundColor Cyan
$envVars = "GCS_BUCKET=$env:GCS_BUCKET,GCP_PROJECT_ID=$ProjectId"
if ($env:FIRESTORE_COLLECTION) {
    $envVars += ",FIRESTORE_COLLECTION=$env:FIRESTORE_COLLECTION"
} else {
    $envVars += ",FIRESTORE_COLLECTION=generators"
}

gcloud run deploy $ServiceName `
  --image $ImageName `
  --region $Region `
  --platform managed `
  --allow-unauthenticated `
  --set-env-vars $envVars `
  --memory 512Mi `
  --cpu 1 `
  --timeout 300 `
  --max-instances 10 `
  --min-instances 0

# Get service URL
$ServiceUrl = gcloud run services describe $ServiceName --region $Region --format 'value(status.url)'

Write-Host ""
Write-Host "✅ Deployment complete!" -ForegroundColor Green
Write-Host "   Service URL: $ServiceUrl" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 Next steps:"
Write-Host "   1. Test the service: curl $ServiceUrl/v1/generators"
Write-Host "   2. Set up API Gateway: .\deploy-api-gateway.ps1 -CloudRunUrl $ServiceUrl"
