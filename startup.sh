#!/bin/bash

# Install Playwright and its browser dependencies
echo "Installing Playwright browsers..."
python -m playwright install --with-deps chromium

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn --bind=0.0.0.0 --timeout 600 --workers=2 app:app