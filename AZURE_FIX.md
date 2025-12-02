# Quick Azure Deployment Fix for Playwright

## The Problem
Playwright browsers aren't installed on Azure App Service by default, causing the error:
```
BrowserType.launch: Executable doesn't exist at /root/.cache/ms-playwright/chromium_headless_shell
```

## Solution Options

### ✅ **Option 1: Use Startup Script (Recommended for App Service)**

1. **In Azure Portal**, go to your App Service
2. Navigate to **Configuration** → **General settings**
3. Set **Startup Command** to:
   ```bash
   bash startup.sh
   ```
4. Click **Save**
5. **Add Application Settings** (Configuration → Application settings):
   - `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true`
   - `WEBSITES_PORT` = `8000`
   - `PLAYWRIGHT_BROWSERS_PATH` = `/tmp/playwright`
   - `FACEBOOK_ACCESS_TOKEN` = *your token*
   - `FLASK_SECRET_KEY` = *your secret key*

6. **Restart** your App Service

The `startup.sh` file will automatically install Playwright browsers on startup.

---

### ✅ **Option 2: Use Docker Container (Most Reliable)**

If Option 1 doesn't work, use Docker:

#### Step 1: Build Docker Image
```bash
cd "c:\Users\Admin\Downloads\Asante Projects\X Test Run for Influencers"
docker build -t influencerapp:latest .
```

#### Step 2: Test Locally
```bash
docker run -p 8000:8000 -e FACEBOOK_ACCESS_TOKEN="your_token" influencerapp:latest
```
Visit http://localhost:8000 to verify it works

#### Step 3: Push to Azure Container Registry (ACR)

```bash
# Login to ACR
az acr login --name yourregistry

# Tag image
docker tag influencerapp:latest yourregistry.azurecr.io/influencerapp:latest

# Push image
docker push yourregistry.azurecr.io/influencerapp:latest
```

#### Step 4: Deploy to Azure Web App

**Option A: Via Azure Portal**
1. Create new Web App or use existing
2. Choose **Container** as publish type
3. Select your ACR image
4. Add environment variables in Configuration

**Option B: Via Azure CLI**
```bash
az webapp create --resource-group yourgroup --plan yourplan --name influencerapp --deployment-container-image-name yourregistry.azurecr.io/influencerapp:latest

# Set environment variables
az webapp config appsettings set --resource-group yourgroup --name influencerapp --settings FACEBOOK_ACCESS_TOKEN="your_token" FLASK_SECRET_KEY="your_key"
```

---

## Verification Steps

### 1. Check Logs
Azure Portal → App Service → Monitoring → **Log stream**

Look for:
```
Installing Playwright browsers...
Chromium 120.0.6099.28 downloaded successfully
Starting Gunicorn...
```

### 2. Test the App
- Visit your Azure URL
- Try the single link analyzer with a test URL
- Check if scraping works

### 3. Monitor Performance
Azure Portal → Metrics

Watch:
- CPU usage
- Memory usage
- Response time

---

## Troubleshooting

### ❌ "Startup script not running"
**Fix:** 
- Ensure file is named `startup.sh` (not .txt)
- Check file has Unix line endings (LF, not CRLF)
- Run in PowerShell:
  ```powershell
  (Get-Content startup.sh -Raw) -replace "`r`n","`n" | Set-Content -NoNewline startup.sh
  ```

### ❌ "Still getting browser not found error"
**Fix:** 
- Use Docker option instead (more reliable)
- Or SSH into app service and manually install:
  ```bash
  python -m playwright install --with-deps chromium
  ```

### ❌ "Out of memory"
**Fix:**
- Scale up to B2 or higher tier
- Reduce Gunicorn workers in startup.sh:
  ```bash
  --workers=1
  ```

### ❌ "Timeout errors"
**Fix:**
- Increase timeout in Configuration → General settings
- Set to 600 seconds (10 minutes)
- Process fewer URLs per batch

---

## Recommended Azure Configuration

### Minimum Requirements:
- **Tier**: B1 Basic ($13/month)
- **Timeout**: 600 seconds
- **Workers**: 1-2

### Recommended Production:
- **Tier**: P1V2 Premium ($73/month)
- **Timeout**: 600 seconds
- **Workers**: 2-4
- **Auto-scaling**: Enabled

---

## Files Changed

✅ **startup.sh** - Installs Playwright on app start
✅ **Dockerfile** - Docker deployment option
✅ **.dockerignore** - Docker build optimization
✅ **AZURE_DEPLOYMENT.md** - Complete deployment guide

---

## Next Steps

1. Choose deployment method (startup script or Docker)
2. Configure Azure settings as described above
3. Deploy application
4. Test functionality
5. Monitor and scale as needed

For detailed instructions, see **AZURE_DEPLOYMENT.md**
