# Deployment

## Overview

- Cloud Run hosts a single service that serves REST (`/v1/...`) and MCP (`/mcp`).
- API Gateway sits in front and enforces Firebase Auth JWTs.
- The app itself does not enforce auth in production; keep it at the gateway.

## Required environment variables

```
GCS_BUCKET=your-bucket
GCS_PROJECT_ID=your-project-id
FIRESTORE_PROJECT_ID=your-project-id
FIRESTORE_DATABASE_ID=(default)
FIRESTORE_COLLECTION=generators
GCS_UPLOAD_URL_EXPIRY_SECONDS=600
```

Local-only (optional):

```
USE_IN_MEMORY_ADAPTERS=true
```

For local GCP access, see `docs/service-account.md`.

## Deploy to Cloud Run

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/constructio-api

gcloud run deploy constructio-api \
  --image gcr.io/YOUR_PROJECT_ID/constructio-api \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars "GCS_BUCKET=...,GCS_PROJECT_ID=...,FIRESTORE_PROJECT_ID=...,FIRESTORE_COLLECTION=generators"
```

## Private Cloud Run (recommended)

Once API Gateway is in place, restrict Cloud Run to internal/gateway traffic:

```bash
gcloud run services update constructio-api \
  --region us-central1 \
  --ingress internal-and-cloud-load-balancing \
  --no-allow-unauthenticated
```

Grant the API Gateway service account permission to invoke the service:

```bash
PROJECT_ID=your-project-id
SERVICE_NAME=constructio-api
GATEWAY_SA=service-${PROJECT_NUMBER}@gcp-sa-apigateway.iam.gserviceaccount.com

gcloud run services add-iam-policy-binding ${SERVICE_NAME} \
  --region us-central1 \
  --member="serviceAccount:${GATEWAY_SA}" \
  --role="roles/run.invoker"
```

## API Gateway (Firebase Auth)

1) Configure API Gateway to validate Firebase JWTs.
2) Restrict Cloud Run to only allow API Gateway invocations.
3) Use the gateway URL for all external traffic.

JWT validation is configured in `api-gateway-config.yaml`. Ensure the issuer and audience match
your Firebase project.

Local test (gateway):

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://your-gateway-url/v1/generators
```

## MCP endpoint

MCP is served by the same app at `/mcp`:

```bash
curl -X POST https://your-gateway-url/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Health checks

Use the API Gateway URL for health checks if you keep the service private.

```bash
curl https://your-gateway-url/v1/generators
```

## Notes

- Keep secrets out of git. Use Secret Manager or env vars.
- For local tests without GCP, set `USE_IN_MEMORY_ADAPTERS=true`.
- If you see 401s from the gateway, confirm Firebase Auth is enabled and the JWT is valid.
