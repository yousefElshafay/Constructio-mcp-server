# Deployment Plan (europe-west1, Artifact Registry)

Project: gen-lang-client-0772504950
Region: europe-west1
Bucket: constructio-mcp-uploads
Firestore DB: constructio-metadata
Collection: generators

## Phase 0 — Preflight & Inventory (read-only)
- Confirm project/region:
  - gcloud config get-value project
  - gcloud config get-value run/region
- Verify APIs enabled:
  - gcloud services list --enabled --project gen-lang-client-0772504950
- Verify Firestore DB:
  - gcloud firestore databases list --project gen-lang-client-0772504950
- Verify bucket:
  - gcloud storage buckets list --project gen-lang-client-0772504950 --filter="name:constructio-mcp-uploads"
- Verify Artifact Registry repo (if already created):
  - gcloud artifacts repositories list --project gen-lang-client-0772504950 --location europe-west1

## Phase 1 — Runtime Service Account + IAM
- Create runtime SA:
  - gcloud iam service-accounts create constructio-runtime --display-name="Constructio Cloud Run" --project gen-lang-client-0772504950
- Grant Firestore access:
  - gcloud projects add-iam-policy-binding gen-lang-client-0772504950 --member="serviceAccount:constructio-runtime@gen-lang-client-0772504950.iam.gserviceaccount.com" --role="roles/datastore.user"
- Grant GCS access:
  - gcloud projects add-iam-policy-binding gen-lang-client-0772504950 --member="serviceAccount:constructio-runtime@gen-lang-client-0772504950.iam.gserviceaccount.com" --role="roles/storage.objectAdmin"
- Grant Token Creator (for Signed URLs):
  - gcloud projects add-iam-policy-binding gen-lang-client-0772504950 --member="serviceAccount:constructio-runtime@gen-lang-client-0772504950.iam.gserviceaccount.com" --role="roles/iam.serviceAccountTokenCreator"
- Verify bindings:
  - gcloud projects get-iam-policy gen-lang-client-0772504950 --flatten="bindings[].members" --filter="constructio-runtime@gen-lang-client-0772504950.iam.gserviceaccount.com"

## Phase 2 — Build & Deploy Cloud Run
- Create Artifact Registry repo (if not exists):
  - gcloud artifacts repositories create constructio --repository-format=docker --location=europe-west1 --project gen-lang-client-0772504950
- Build & Push image (Cloud Build):
  - gcloud builds submit --tag europe-west1-docker.pkg.dev/gen-lang-client-0772504950/constructio/constructio-api --project gen-lang-client-0772504950
- Deploy Cloud Run:
  - gcloud run deploy constructio-mcp-server \
      --image europe-west1-docker.pkg.dev/gen-lang-client-0772504950/constructio/constructio-api \
      --region europe-west1 \
      --project gen-lang-client-0772504950 \
      --service-account constructio-runtime@gen-lang-client-0772504950.iam.gserviceaccount.com \
      --set-env-vars "GCS_BUCKET=constructio-mcp-uploads,GCS_PROJECT_ID=gen-lang-client-0772504950,FIRESTORE_PROJECT_ID=gen-lang-client-0772504950,FIRESTORE_DATABASE_ID=constructio-metadata,FIRESTORE_COLLECTION=generators,GCS_UPLOAD_URL_EXPIRY_SECONDS=600,USE_IN_MEMORY_ADAPTERS=false,GCS_SIGNER_SERVICE_ACCOUNT=constructio-runtime@gen-lang-client-0772504950.iam.gserviceaccount.com" \
      --no-allow-unauthenticated
- Verify direct Cloud Run:
  - gcloud run services describe constructio-mcp-server --region europe-west1 --project gen-lang-client-0772504950 --format="value(status.url)"
  - curl <RUN_URL>/health
  - curl <RUN_URL>/v1/generators

## Phase 3 — API Gateway (JWT Auth)
- Update api-gateway-config.yaml with:
  - Cloud Run backend URL(s)
  - Firebase JWT auth (OpenAPI 2.0)
  - x-google-backend.jwt_audience set to Cloud Run URL
- Deploy gateway config:
  - gcloud api-gateway apis create constructio-api --project gen-lang-client-0772504950
  - gcloud api-gateway api-configs create constructio-api-config-<ts> \
      --api=constructio-api \
      --openapi-spec=api-gateway-config.yaml \
      --project gen-lang-client-0772504950
- Create gateway:
  - gcloud api-gateway gateways create constructio-gateway \
      --api=constructio-api \
      --api-config=constructio-api-config-<ts> \
      --location europe-west1 \
      --project gen-lang-client-0772504950
- Enable managed service + Service Control:
  - gcloud services enable constructio-api-<hash>.apigateway.gen-lang-client-0772504950.cloud.goog --project gen-lang-client-0772504950
  - gcloud services enable servicecontrol.googleapis.com servicemanagement.googleapis.com --project gen-lang-client-0772504950
  - gcloud projects add-iam-policy-binding gen-lang-client-0772504950 \
      --member="serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-apigateway.iam.gserviceaccount.com" \
      --role="roles/servicemanagement.serviceController"
- Lock Cloud Run ingress + allow gateway invoker:
  - gcloud run services update constructio-mcp-server --region europe-west1 --project gen-lang-client-0772504950 --ingress all
  - PROJECT_NUMBER=$(gcloud projects describe gen-lang-client-0772504950 --format="value(projectNumber)")
  - GATEWAY_SA=service-${PROJECT_NUMBER}@gcp-sa-apigateway.iam.gserviceaccount.com
  - gcloud run services add-iam-policy-binding constructio-mcp-server \
      --region europe-west1 \
      --project gen-lang-client-0772504950 \
      --member="serviceAccount:${GATEWAY_SA}" \
      --role="roles/run.invoker"
- Verify gateway:
  - gcloud api-gateway gateways describe constructio-gateway --location europe-west1 --project gen-lang-client-0772504950 --format="value(defaultHostname)"
  - curl -H "Authorization: Bearer <ID_TOKEN>" https://<GATEWAY_HOST>/v1/generators

### Current values (this environment)
- Managed service:
  - constructio-api-2yz3hjonbmxna.apigateway.gen-lang-client-0772504950.cloud.goog
- Gateway host:
  - constructio-gateway-9bnjp9au.ew.gateway.dev

## Phase 4 — Firebase Auth (JWT-only)
- Update gateway config:
  - x-google-issuer: https://securetoken.google.com/gen-lang-client-0772504950
  - x-google-audiences: gen-lang-client-0772504950
- Deploy new API config + update gateway
- Verify with JWT:
  - curl -H "Authorization: Bearer <ID_TOKEN>" https://<GATEWAY_HOST>/v1/generators

## Phase 5 — CI/CD
- Choose GitHub Actions or Cloud Build (docs/cicd.md)
- Create CI/CD SA and roles:
  - roles/run.admin
  - roles/iam.serviceAccountUser
  - roles/apigateway.admin
  - roles/artifactregistry.writer
- Configure secrets/substitutions
- Verify pipeline: build, deploy, gateway update, health check

## Verification Checklist
- gcloud services list --enabled --project gen-lang-client-0772504950
- gcloud run services describe constructio-mcp-server --region europe-west1 --project gen-lang-client-0772504950
- gcloud api-gateway gateways describe constructio-gateway --location europe-west1 --project gen-lang-client-0772504950
- gcloud storage buckets list --project gen-lang-client-0772504950 --filter="name:constructio-mcp-uploads"
- gcloud firestore databases list --project gen-lang-client-0772504950
