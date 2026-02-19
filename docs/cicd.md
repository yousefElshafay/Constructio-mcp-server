# CI/CD Setup Instructions

## Overview

This project uses GitHub Actions with Workload Identity Federation (WIF).

The pipeline automatically:
- Run tests on every push
- Build Docker image
- Deploy to Cloud Run
- Update API Gateway (if config changed)

---

## GitHub Actions (WIF)

### Step 1: Create Service Account

```powershell
# Set your project ID
$PROJECT_ID = "<PROJECT_ID>"

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
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SA_EMAIL" `
  --role="roles/apigateway.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID `
  --member="serviceAccount:$SA_EMAIL" `
  --role="roles/artifactregistry.writer"
```

### Step 2: Workload Identity Federation (WIF)

Create a Workload Identity Pool and Provider, then allow the GitHub repo to
impersonate the service account. See `docs/gcp_setup.md` for the exact commands.

### Step 3: Add GitHub Secrets and Variables

Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**.
Add repository secrets for deploy settings and WIF identifiers, and variables
for non-sensitive values. Do not use service account keys.

### Step 4: Push to Main Branch

```bash
git add .
git commit -m "feat: add CI/CD pipeline"
git push origin main
```

The workflow will automatically run! View it at:
- **GitHub** → **Actions** tab

### Step 5: Monitor Deployment

Watch the workflow run through:
1. Run Tests
2. Build Docker Image
3. Deploy to Cloud Run
4. Update API Gateway (if changed)

---

## Configuration

### Customize Cloud Run Settings

Adjust deploy settings via GitHub Actions secrets/variables rather than
editing the workflow.

### Disable API Gateway Updates

If you don't want to update API Gateway on every deploy, remove the
"Update API Gateway" step from the workflow.

---

## Health Checks

The health endpoint is at `/health`:

```bash
curl https://<RUN_URL>/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "<SERVICE_NAME>"
}
```

---

## Rollback

### Rollback Cloud Run to Previous Revision

```powershell
# List revisions
gcloud run revisions list `
  --service=<SERVICE_NAME> `
  --region=<REGION>

# Rollback to specific revision
gcloud run services update-traffic <SERVICE_NAME> `
  --to-revisions=<SERVICE_NAME>-00042-xyz=100 `
  --region=<REGION>
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
gcloud run services logs tail <SERVICE_NAME> --region=<REGION>
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
gcloud projects add-iam-policy-binding <PROJECT_ID> `
  --member="serviceAccount:<SERVICE_ACCOUNT>" `
  --role="roles/run.admin"
```

### Health Check Fails

**Symptom:** Health check returns 503

**Solutions:**
- Service might be cold starting (wait 30s)
- Check service logs:
  ```bash
  gcloud run services logs tail <SERVICE_NAME> --region=<REGION>
  ```
- Test endpoint manually:
  ```bash
  curl -v https://<RUN_URL>/health
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
  gcloud projects add-iam-policy-binding <PROJECT_ID> \
    --member="serviceAccount:<SERVICE_ACCOUNT>" \
    --role="roles/apigateway.admin"
  ```

---

## Multi-Environment Setup (Advanced)

### Staging Environment

Create a separate workflow for staging:

1. Create `.github/workflows/deploy-staging.yml`
2. Modify to deploy to `<SERVICE_NAME>-staging`
3. Trigger on push to `develop` branch

**Quick setup:**
```yaml
# .github/workflows/deploy-staging.yml
name: Deploy to Staging
on:
  push:
    branches: [develop]

env:
  SERVICE_NAME: <SERVICE_NAME>-staging
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
  SERVICE_NAME: <SERVICE_NAME>-pr-${{ github.event.pull_request.number }}
```

---

## Best Practices

1. Always run tests locally before pushing
2. Use feature branches and merge via PR
3. Review GitHub Actions logs after deployment
4. Monitor Cloud Run metrics in GCP Console
5. Set up alerting for production failures
6. Keep secrets in Secret Manager (not in code)
7. Tag releases for easy rollback

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

### Useful Commands
```powershell
# View service status
gcloud run services describe <SERVICE_NAME> --region=<REGION>

# Stream logs
gcloud run services logs tail <SERVICE_NAME> --region=<REGION>

# Test health endpoint
curl https://<RUN_URL>/health
```
