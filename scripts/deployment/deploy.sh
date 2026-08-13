#!/bin/bash

# TSE Analysis Native Python Deployment Script for Linux/macOS
# Run this script to deploy the application natively

echo "🚀 Starting TSE Analysis Native Deployment..."

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "❌ Python is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Use python3 if available, otherwise python
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Check if application can start
echo "🔍 Testing application startup..."
timeout 10s $PYTHON_CMD app.py &
APP_PID=$!
sleep 5

if kill -0 $APP_PID 2>/dev/null; then
    kill $APP_PID
    echo "✅ Application started successfully!"
else
    echo "❌ Application failed to start"
    exit 1
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "🌐 To start the application, run: python app.py"
echo "📊 API will be available at: http://localhost:5000"
echo "🔧 Management Panel: http://localhost:5000/management"

echo ""
echo "📋 Useful commands:"
echo "  • Start: python app.py"
echo "  • Stop: Ctrl+C in the terminal"
echo "  • Test: python -m pytest tests/"