# Azure App Service Configuration

## Post-Deployment Configuration Steps

After deploying to Azure, you need to configure the following settings in the Azure Portal:

### 1. **Add Startup Command**

In Azure Portal → Your App Service → Configuration → General settings:

**Startup Command:**
```bash
bash startup.sh
```

### 2. **Add Application Settings (Environment Variables)**

In Azure Portal → Your App Service → Configuration → Application settings:

Add these settings:

| Name | Value |
|------|-------|
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` |
| `WEBSITES_PORT` | `8000` |
| `FACEBOOK_ACCESS_TOKEN` | Your Facebook API token |
| `FLASK_SECRET_KEY` | Your secret key |
| `PLAYWRIGHT_BROWSERS_PATH` | `/tmp/playwright` |
| `PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD` | `0` |

### 3. **Increase Timeout Settings**

In Azure Portal → Your App Service → Configuration → General settings:

- **Request Timeout**: Set to `600` seconds (10 minutes)
- This allows Playwright scrapers enough time to complete

### 4. **Scale Up App Service Plan (if needed)**

For better Playwright performance:

- Go to Azure Portal → Your App Service → Scale up (App Service plan)
- Consider **B2** or higher tier for:
  - More CPU/RAM for browser instances
  - Better performance
  - Reduced timeouts

**Recommended tiers:**
- **Development**: B1 or B2
- **Production**: P1V2 or P2V2

### 5. **Enable Logging**

In Azure Portal → Your App Service → Monitoring → App Service logs:

- **Application Logging**: On (Filesystem)
- **Detailed Error Messages**: On
- **Failed Request Tracing**: On

View logs at: App Service → Monitoring → Log stream

### 6. **Install System Dependencies**

The `startup.sh` script automatically installs Playwright browsers with system dependencies using:
```bash
python -m playwright install --with-deps chromium
```

This installs:
- Chromium browser
- System libraries (libgobject, libglib, etc.)
- Font dependencies
- Other required packages

## Alternative: Use Docker Container

If the above steps don't work or you need more control, consider using a Docker container:

### 1. Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \\
    wget \\
    gnupg \\
    ca-certificates \\
    fonts-liberation \\
    libasound2 \\
    libatk-bridge2.0-0 \\
    libatk1.0-0 \\
    libatspi2.0-0 \\
    libcairo2 \\
    libcups2 \\
    libdbus-1-3 \\
    libdrm2 \\
    libgbm1 \\
    libglib2.0-0 \\
    libgtk-3-0 \\
    libnspr4 \\
    libnss3 \\
    libpango-1.0-0 \\
    libx11-6 \\
    libxcb1 \\
    libxcomposite1 \\
    libxdamage1 \\
    libxext6 \\
    libxfixes3 \\
    libxrandr2 \\
    xdg-utils \\
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN python -m playwright install chromium

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind=0.0.0.0:8000", "--timeout", "600", "--workers", "2", "app:app"]
```

### 2. Build and push to Azure Container Registry:

```bash
# Build image
docker build -t influencerapp .

# Tag for ACR
docker tag influencerapp youracr.azurecr.io/influencerapp:latest

# Push to ACR
docker push youracr.azurecr.io/influencerapp:latest
```

### 3. Deploy container to Azure Web App

In Azure Portal:
- Create new Web App
- Choose **Docker Container** as publish method
- Select your ACR image

## Troubleshooting

### Error: "BrowserType.launch: Executable doesn't exist"

**Solutions:**

1. **Verify startup script runs:**
   - Check Azure logs: App Service → Log stream
   - Look for "Installing Playwright browsers..." message

2. **Manually install via SSH:**
   ```bash
   # SSH into Azure App Service
   python -m playwright install --with-deps chromium
   ```

3. **Check permissions:**
   - Ensure `/tmp/playwright` directory is writable
   - Azure App Service uses `/home` for persistent storage

4. **Increase deployment timeout:**
   - Add to Application Settings:
     ```
     WEBSITE_SCM_COMMAND_IDLE_TIMEOUT = 1800
     ```

### Error: "Timeout waiting for..."

**Solutions:**

1. **Increase app timeout:**
   - Configuration → General settings → Request Timeout = 600

2. **Scale up tier:**
   - Current tier might be too slow
   - Upgrade to B2/P1V2 or higher

3. **Optimize scraping:**
   - Already optimized in code
   - Consider processing fewer URLs per batch

### Error: "Out of memory"

**Solutions:**

1. **Scale up:**
   - Need more RAM for browser instances
   - Minimum B2 tier recommended

2. **Reduce workers:**
   - Edit startup.sh: `--workers=1`

3. **Add swap space** (Docker only):
   ```dockerfile
   RUN dd if=/dev/zero of=/swapfile bs=1M count=1024 && \\
       chmod 600 /swapfile && \\
       mkswap /swapfile && \\
       swapon /swapfile
   ```

## Performance Tips

1. **Use caching** (already implemented)
   - Reduces repeated scraping
   - Faster response times

2. **Process in batches:**
   - Split large CSV files
   - Process 10-20 URLs at a time

3. **Monitor resource usage:**
   - Azure Portal → Metrics
   - Watch CPU/Memory usage
   - Scale up if consistently high

4. **Consider Azure Functions:**
   - For background processing
   - Better for long-running scrapes
   - Pay-per-execution model

## Cost Optimization

### Free/Shared Tier (F1)
- ❌ **Not recommended** - Too limited for Playwright
- No custom startup command support
- Insufficient resources

### Basic Tier (B1-B3)
- ✅ **Recommended for development**
- B1: $13/month - Minimum for Playwright
- B2: $26/month - Better performance
- B3: $52/month - Production-ready

### Standard/Premium Tier (S1-P3V3)
- ✅ **Recommended for production**
- Auto-scaling support
- Better performance
- Staging slots

## Quick Setup Checklist

- [ ] Rename `startup.txt` to `startup.sh`
- [ ] Add startup command in Azure Portal: `bash startup.sh`
- [ ] Add environment variables (FACEBOOK_ACCESS_TOKEN, etc.)
- [ ] Set request timeout to 600 seconds
- [ ] Enable application logging
- [ ] Deploy application
- [ ] Check logs for Playwright installation
- [ ] Test with single link first
- [ ] Monitor resource usage
- [ ] Scale up if needed

## Support Resources

- [Azure App Service Python Docs](https://docs.microsoft.com/azure/app-service/quickstart-python)
- [Playwright Azure Deployment](https://playwright.dev/python/docs/ci#azure-pipelines)
- [Azure Container Registry](https://docs.microsoft.com/azure/container-registry/)
