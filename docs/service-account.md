# Service Account (Local GCP Access)

Use this only if you want to run against real Firestore/GCS locally.

## Create a service account

```bash
PROJECT_ID=<PROJECT_ID>
SA_NAME=constructio-api

gcloud iam service-accounts create ${SA_NAME} \
  --display-name="Constructio API" \
  --project=${PROJECT_ID}
```

## Grant roles

```bash
SA_EMAIL=${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/storage.objectAdmin"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountTokenCreator"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/datastore.user"
```

## Create a key

```bash
gcloud iam service-accounts keys create gcp-key.json \
  --iam-account=${SA_EMAIL} \
  --project=${PROJECT_ID}
```

## Configure local env

```
USE_IN_MEMORY_ADAPTERS=false
GOOGLE_APPLICATION_CREDENTIALS=gcp-key.json
```

Keep `gcp-key.json` out of version control.
