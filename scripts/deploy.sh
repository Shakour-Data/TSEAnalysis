#!/bin/bash
# TSEAnalysis Deployment Script for Linux/Unix

# Ensure we are in the project root
cd "$(dirname "$0")/.."

set -e

echo "==== Checking Requirements ===="
if ! command -v python3 &> /dev/null; then
    echo "CRITICAL: Python3 is not installed."
    exit 1
fi

echo "==== Setting up Virtual Environment ===="
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

echo "==== Installing Dependencies ===="
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install flask flask-caching pandas numpy requests matplotlib ta tls-client curl_cffi jdatetime
    pip freeze > requirements.txt
fi

echo "==== Deployment Complete ===="
echo "To start the server: python3 app.py"
echo "------------------------------------"
python3 app.py
