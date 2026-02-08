#!/bin/bash

# Service Manager Development Environment Setup
# This script sets up the complete development environment

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON="${PYTHON:-python3}"

echo "=================================="
echo "Service Manager Setup"
echo "=================================="
echo ""

# Check Python
echo "Checking Python installation..."
if ! command -v $PYTHON &> /dev/null; then
    echo "ERROR: Python is not installed"
    exit 1
fi

PYTHON_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
echo "✓ Python $PYTHON_VERSION found"

# Create virtual environment (optional)
if [ ! -d "$SCRIPT_DIR/venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    $PYTHON -m venv "$SCRIPT_DIR/venv"
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
if [ -f "$SCRIPT_DIR/venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source "$SCRIPT_DIR/venv/bin/activate"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -q -r "$SCRIPT_DIR/requirements.txt"
echo "✓ Python dependencies installed"

# Create logs directory
echo ""
echo "Setting up directories..."
mkdir -p "$SCRIPT_DIR/logs"
echo "✓ Logs directory ready"

# Check Node.js for frontend
echo ""
echo "Checking Node.js installation..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✓ Node.js $NODE_VERSION found"
    
    echo ""
    echo "Setting up frontend..."
    cd "$SCRIPT_DIR/frontend"
    
    if [ ! -d "node_modules" ]; then
        echo "Installing npm dependencies..."
        npm install --legacy-peer-deps --silent
        echo "✓ Frontend dependencies installed"
    else
        echo "✓ Frontend dependencies already installed"
    fi
else
    echo "⚠ Node.js not found (optional for backend-only mode)"
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "To start the development server:"
echo "  ./dev-start.sh"
echo ""
echo "Or start services individually:"
echo "  ./dev-start.sh backend   # Backend only"
echo "  ./dev-start.sh frontend  # Frontend only"
echo ""
