#!/bin/bash

# LightRAG Mini Startup Script

echo "Starting LightRAG Mini..."
echo "========================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Please create one based on the provided template."
    echo "The server may not work correctly without proper configuration."
fi

# Create necessary directories
mkdir -p cache
mkdir -p inputs

# Start the server
echo "Starting LightRAG Mini server..."
echo "Server will be available at: http://localhost:8000"
echo "API documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py