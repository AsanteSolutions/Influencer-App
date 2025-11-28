# Use official Python base
FROM python:3.11-slim

# Install OS packages Playwright/Chromium need
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libasound2 \
    libgbm1 \
    libgtk-3-0 \
    libpangocairo-1.0-0 \
    curl \
    fonts-liberation \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Set working dir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy application files
COPY . /app

# Install Playwright browsers and other build steps
# (Note: we must run playwright install after pip installs playwright)
RUN python -m playwright install chromium

# Expose port that App Service will map (use 80)
EXPOSE 80

# Start app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app", "--workers", "4", "--threads", "2"]