# CI/CD Setup Instructions

## Overview

This project has two CI/CD options:
1. **GitHub Actions** - Best for GitHub-hosted repositories
2. **Cloud Build** - Native GCP solution, works with any Git provider

Both pipelines automatically:
- ✅ Run tests on every push
- ✅ Build Docker image
- ✅ Deploy to Cloud Run
- ✅ Update API Gateway (if config changed)
- ✅ Run health checks

---

## Option 1: GitHub Actions (Recommended for GitHub)

### Step 1: Create Service Account

```powershell
# Set your project ID
$PROJECT_ID = "your-gcp-project-id"

# Create service account
gcloud iam service-accounts create github-actions `
  --display-name="GitHub Actions CI/CD" `
  --project=$PROJECT_ID

# Grant required permissions
$SA_EMAIL = "github-actions@$PROJECT_ID.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SA_EMAIL" `
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SA_EMAIL" `
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SA_EMAIL" `
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SA_EMAIL" `
  --role="roles/apigateway.admin"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json `
  --iam-account=$SA_EMAIL `
  --project=$PROJECT_ID
```

### Step 2: Add GitHub Secrets

1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret** and add:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `GCP_PROJECT_ID` | `your-gcp-project-id` | Your GCP project ID |
| `GCP_SA_KEY` | Contents of `github-actions-key.json` | Service account JSON key |
| `GCS_BUCKET` | `your-bucket-name` | GCS bucket for artifacts |
| `FIRESTORE_COLLECTION` | `generators` | Firestore collection name |

**To get the SA key contents:**
```powershell
Get-Content github-actions-key.json | Out-String
# Copy the entire output and paste into GCP_SA_KEY secret
```

### Step 3: Push to Main Branch

```bash
git add .
git commit -m "feat: add CI/CD pipeline"
git push origin main
```

The workflow will automatically run! View it at:
- **GitHub** → **Actions** tab

### Step 4: Monitor Deployment

Watch the workflow run through:
1. ✅ Run Tests
2. ✅ Build Docker Image
3. ✅ Deploy to Cloud Run
4. ✅ Update API Gateway (if changed)
5. ✅ Deployment Summary

---

## Option 2: Cloud Build (Native GCP)

### Step 1: Enable Cloud Build API

```powershell
gcloud services enable cloudbuild.googleapis.com --project=YOUR_PROJECT_ID
```

### Step 2: Grant Cloud Build Permissions

```powershell
$PROJECT_ID = "your-gcp-project-id"
$PROJECT_NUMBER = (gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
$CB_SA = "${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$CB_SA" `
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$CB_SA" `
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$CB_SA" `
  --role="roles/apigateway.admin"
```

### Step 3: Connect GitHub Repository

**Via gcloud CLI:**
```powershell
gcloud builds triggers create github `
  --repo-name=Constructio-mcp-server `
  --repo-owner=YOUR_GITHUB_USERNAME `
  --branch-pattern="^main$" `
  --build-config=cloudbuild.yaml `
  --substitutions _GCS_BUCKET=your-bucket-name,_FIRESTORE_COLLECTION=generators
```

**Via Console:**
1. Go to [Cloud Build → Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click **Create Trigger**
3. Connect your GitHub repository
4. Configure:
   - **Name:** `deploy-main`
   - **Event:** Push to branch
   - **Branch:** `^main$`
   - **Build configuration:** `cloudbuild.yaml`
   - **Substitution variables:**
     - `_GCS_BUCKET` = `your-bucket-name`
     - `_FIRESTORE_COLLECTION` = `generators`

### Step 4: Test the Trigger

```bash
git add .
git commit -m "feat: test cloud build trigger"
git push origin main
```

Monitor the build:
```powershell
# List recent builds
gcloud builds list --limit=5

# Stream logs for specific build
gcloud builds log BUILD_ID --stream
```

Or view in [Cloud Build Console](https://console.cloud.google.com/cloud-build/builds)

---

## Configuration

### Customize Cloud Run Settings

Edit `cloudbuild.yaml` substitutions:

```yaml
substitutions:
  _SERVICE_NAME: 'constructio-mcp-server'  # Service name
  _REGION: 'us-central1'                   # Deployment region
  _MEMORY: '512Mi'                         # Memory allocation
  _CPU: '1'                                # CPU allocation
  _MAX_INSTANCES: '10'                     # Max instances
  _MIN_INSTANCES: '0'                      # Min instances (0 = scale to zero)
  _UPDATE_GATEWAY: 'true'                  # Set to 'false' to skip gateway updates
```

### Disable API Gateway Updates

If you don't want to update API Gateway on every deploy:

**GitHub Actions:** Comment out the `update-gateway` job
**Cloud Build:** Set `_UPDATE_GATEWAY: 'false'` in substitutions

---

## Health Checks

The health endpoint is at `/health`:

```bash
curl https://your-service.run.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "constructio-mcp-server"
}
```

---

## Rollback

### Rollback Cloud Run to Previous Revision

```powershell
# List revisions
gcloud run revisions list `
  --service=constructio-mcp-server `
  --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic constructio-mcp-server `
  --to-revisions=constructio-mcp-server-00042-xyz=100 `
  --region=us-central1
```

### Rollback GitHub Actions Deployment

1. Find the previous successful commit
2. Revert or push the old code:
   ```bash
   git revert HEAD
   git push origin main
   ```

---

## Monitoring

### View Logs

**Cloud Run:**
```powershell
gcloud run services logs tail constructio-mcp-server --region=us-central1
```

**Cloud Build:**
```powershell
gcloud builds log BUILD_ID --stream
```

### Set Up Alerts

Create an alert for failed deployments:

```powershell
gcloud alpha monitoring policies create `
  --notification-channels=CHANNEL_ID `
  --display-name="Failed Deployments" `
  --condition-display-name="Deployment failure" `
  --condition-threshold-value=1 `
  --condition-threshold-duration=60s
```

---

## Troubleshooting

### Tests Fail

**Symptom:** Pipeline fails at test step

**Solution:**
```bash
# Run tests locally
uv pip install -e ".[dev]"
pytest tests/ -v
```

Fix failing tests, commit, and push again.

### Docker Build Fails

**Symptom:** Build step fails

**Solutions:**
- Check Dockerfile syntax
- Verify all dependencies are in `pyproject.toml`
- Test locally:
  ```bash
  docker build -t test .
  docker run -p 8080:8080 test
  ```

### Deployment Fails with "Permission Denied"

**Symptom:** Deploy step fails with IAM errors

**Solution:**
```powershell
# Re-grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID `
  --member="serviceAccount:SA_EMAIL" `
  --role="roles/run.admin"
```

### Health Check Fails

**Symptom:** Health check returns 503

**Solutions:**
- Service might be cold starting (wait 30s)
- Check service logs:
  ```bash
  gcloud run services logs tail constructio-mcp-server --region=us-central1
  ```
- Test endpoint manually:
  ```bash
  curl -v https://your-service.run.app/health
  ```

### API Gateway Update Fails

**Symptom:** Gateway update step fails

**Solutions:**
- Config name might already exist (safe to ignore)
- Check if API Gateway API is enabled:
  ```bash
  gcloud services enable apigateway.googleapis.com
  ```
- Verify you have permissions:
  ```bash
  gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:SA_EMAIL" \
    --role="roles/apigateway.admin"
  ```

---

## Multi-Environment Setup (Advanced)

### Staging Environment

Create a separate workflow for staging:

1. Create `.github/workflows/deploy-staging.yml`
2. Modify to deploy to `constructio-mcp-server-staging`
3. Trigger on push to `develop` branch

**Quick setup:**
```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging
on:
  push:
    branches: [develop]

env:
  SERVICE_NAME: constructio-mcp-server-staging
  # ... rest same as deploy.yml
```

### Preview Environments (Pull Requests)

Deploy each PR to a temporary environment:

```yaml
# In .github/workflows/deploy.yml
on:
  pull_request:
    branches: [main]

env:
  SERVICE_NAME: constructio-pr-${{ github.event.pull_request.number }}
```

---

## Best Practices

1. **Always run tests locally** before pushing
2. **Use feature branches** and merge via PR
3. **Review Cloud Build logs** after deployment
4. **Monitor Cloud Run metrics** in GCP Console
5. **Set up alerting** for production failures
6. **Keep secrets in Secret Manager** (not in code)
7. **Tag releases** for easy rollback:
   ```bash
   git tag -a v1.0.0 -m "Release 1.0.0"
   git push origin v1.0.0
   ```

---

## Next Steps

- [ ] Test the pipeline with a commit
- [ ] Set up staging environment
- [ ] Configure monitoring alerts
- [ ] Set up Cloud Armor for DDoS protection
- [ ] Enable Cloud CDN for static assets
- [ ] Set up custom domain with Cloud Load Balancer

---

## Quick Reference

### GitHub Actions
- **Workflow file:** `.github/workflows/deploy.yml`
- **View runs:** GitHub → Actions tab
- **Re-run failed:** Click "Re-run failed jobs"

### Cloud Build
- **Config file:** `cloudbuild.yaml`
- **View builds:** [Cloud Build Console](https://console.cloud.google.com/cloud-build/builds)
- **Trigger manually:** `gcloud builds submit --config=cloudbuild.yaml`

### Useful Commands
```powershell
# View service status
gcloud run services describe constructio-mcp-server --region=us-central1

# View recent builds
gcloud builds list --limit=10

# Stream logs
gcloud run services logs tail constructio-mcp-server --region=us-central1

# Test health endpoint
curl https://your-service.run.app/health
```
