# Deployment Plan (<REGION>, Artifact Registry)

Project: <PROJECT_ID>
Region: <REGION>
Bucket: <GCS_BUCKET>
Firestore DB: <FIRESTORE_DB>
Collection: <FIRESTORE_COLLECTION>

## Phase 0 — Preflight & Inventory (read-only)
- Confirm project/region:
  - gcloud config get-value project
  - gcloud config get-value run/region
- Verify APIs enabled:
  - gcloud services list --enabled --project <PROJECT_ID>
- Verify Firestore DB:
  - gcloud firestore databases list --project <PROJECT_ID>
- Verify bucket:
  - gcloud storage buckets list --project <PROJECT_ID> --filter="name:<GCS_BUCKET>"
- Verify Artifact Registry repo (if already created):
  - gcloud artifacts repositories list --project <PROJECT_ID> --location <REGION>

## Phase 1 — Runtime Service Account + IAM
- Create runtime SA:
  - gcloud iam service-accounts create constructio-runtime --display-name="Constructio Cloud Run" --project <PROJECT_ID>
- Grant Firestore access:
  - gcloud projects add-iam-policy-binding <PROJECT_ID> --member="serviceAccount:<RUNTIME_SA_EMAIL>" --role="roles/datastore.user"
- Grant GCS access:
  - gcloud projects add-iam-policy-binding <PROJECT_ID> --member="serviceAccount:<RUNTIME_SA_EMAIL>" --role="roles/storage.objectAdmin"
- Grant Token Creator (for Signed URLs):
  - gcloud projects add-iam-policy-binding <PROJECT_ID> --member="serviceAccount:<RUNTIME_SA_EMAIL>" --role="roles/iam.serviceAccountTokenCreator"
- Verify bindings:
  - gcloud projects get-iam-policy <PROJECT_ID> --flatten="bindings[].members" --filter="<RUNTIME_SA_EMAIL>"

## Phase 2 — Build & Deploy Cloud Run
- Create Artifact Registry repo (if not exists):
  - gcloud artifacts repositories create constructio --repository-format=docker --location <REGION> --project <PROJECT_ID>
- Build & Push image (Docker buildx):
  - docker build -t <AR_REPO>/constructio-api:latest .
  - docker push <AR_REPO>/constructio-api:latest
- Deploy Cloud Run:
  - gcloud run deploy <SERVICE_NAME> \
      --image <AR_REPO>/constructio-api \
      --region <REGION> \
      --project <PROJECT_ID> \
      --service-account <RUNTIME_SA_EMAIL> \
      --set-env-vars "GCS_BUCKET=<GCS_BUCKET>,GCS_PROJECT_ID=<PROJECT_ID>,FIRESTORE_PROJECT_ID=<PROJECT_ID>,FIRESTORE_DATABASE_ID=<FIRESTORE_DB>,FIRESTORE_COLLECTION=<FIRESTORE_COLLECTION>,GCS_UPLOAD_URL_EXPIRY_SECONDS=600,USE_IN_MEMORY_ADAPTERS=false,GCS_SIGNER_SERVICE_ACCOUNT=<RUNTIME_SA_EMAIL>" \
      --no-allow-unauthenticated
- Verify direct Cloud Run:
  - gcloud run services describe <SERVICE_NAME> --region <REGION> --project <PROJECT_ID> --format="value(status.url)"
  - curl <RUN_URL>/health
  - curl <RUN_URL>/v1/generators

## Phase 3 — API Gateway (JWT Auth)
- Update api-gateway-config.yaml with:
  - Cloud Run backend URL(s)
  - Firebase JWT auth (OpenAPI 2.0)
  - x-google-backend.jwt_audience set to Cloud Run URL
- Deploy gateway config:
  - gcloud api-gateway apis create <API_ID> --project <PROJECT_ID>
  - gcloud api-gateway api-configs create <API_CONFIG_ID> \
      --api=<API_ID> \
      --openapi-spec=api-gateway-config.yaml \
      --project <PROJECT_ID>
- Create gateway:
  - gcloud api-gateway gateways create <GATEWAY_NAME> \
      --api=<API_ID> \
      --api-config=<API_CONFIG_ID> \
      --location <REGION> \
      --project <PROJECT_ID>
- Enable managed service + Service Control:
  - gcloud services enable <MANAGED_SERVICE> --project <PROJECT_ID>
  - gcloud services enable servicecontrol.googleapis.com servicemanagement.googleapis.com --project <PROJECT_ID>
  - gcloud projects add-iam-policy-binding <PROJECT_ID> \
      --member="serviceAccount:service-<PROJECT_NUMBER>@gcp-sa-apigateway.iam.gserviceaccount.com" \
      --role="roles/servicemanagement.serviceController"
- Lock Cloud Run ingress + allow gateway invoker:
  - gcloud run services update <SERVICE_NAME> --region <REGION> --project <PROJECT_ID> --ingress all
  - PROJECT_NUMBER=$(gcloud projects describe <PROJECT_ID> --format="value(projectNumber)")
  - GATEWAY_SA=service-${PROJECT_NUMBER}@gcp-sa-apigateway.iam.gserviceaccount.com
  - gcloud run services add-iam-policy-binding <SERVICE_NAME> \
      --region <REGION> \
      --project <PROJECT_ID> \
      --member="serviceAccount:${GATEWAY_SA}" \
      --role="roles/run.invoker"
- Verify gateway:
  - gcloud api-gateway gateways describe <GATEWAY_NAME> --location <REGION> --project <PROJECT_ID> --format="value(defaultHostname)"
  - curl -H "Authorization: Bearer <ID_TOKEN>" https://<GATEWAY_HOST>/v1/generators

## Phase 4 — Firebase Auth (JWT-only)
- Update gateway config:
  - x-google-issuer: https://securetoken.google.com/<FIREBASE_PROJECT_ID>
  - x-google-audiences: <FIREBASE_PROJECT_ID>
- Deploy new API config + update gateway
- Verify with JWT:
  - curl -H "Authorization: Bearer <ID_TOKEN>" https://<GATEWAY_HOST>/v1/generators

## Phase 5 — CI/CD
- GitHub Actions with WIF (docs/cicd.md)
- Create CI/CD SA and roles:
  - roles/run.admin
  - roles/iam.serviceAccountUser
  - roles/apigateway.admin
  - roles/artifactregistry.writer
- Configure secrets/substitutions
- Verify pipeline: build, deploy, gateway update, health check

## Verification Checklist
- gcloud services list --enabled --project <PROJECT_ID>
- gcloud run services describe <SERVICE_NAME> --region <REGION> --project <PROJECT_ID>
- gcloud api-gateway gateways describe <GATEWAY_NAME> --location <REGION> --project <PROJECT_ID>
- gcloud storage buckets list --project <PROJECT_ID> --filter="name:<GCS_BUCKET>"
- gcloud firestore databases list --project <PROJECT_ID>
