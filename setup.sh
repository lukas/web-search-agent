#!/bin/bash

set -e

echo "Setting up Web Search Agent environment..."

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install python3 first."
    echo "On Ubuntu/Debian: apt-get install python3 python3-pip python3-venv"
    echo "On Alpine: apk add python3 py3-pip"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install Playwright (required by CLAUDE.md guidelines)
echo "Installing Playwright..."
pip install playwright pytest-playwright

# Install Playwright browsers (skip system dependencies that require root)
echo "Installing Playwright browsers..."
playwright install --with-deps || {
    echo "Warning: Could not install system dependencies. Installing browsers only..."
    playwright install
}

# Make sure pytest can find the modules
export PYTHONPATH="${PYTHONPATH}:."

# Run tests to verify setup
echo "Running tests to verify setup..."
pytest -v --tb=short --timeout=3

echo "Setup complete! Environment is ready for Web Search Agent."
echo ""
echo "To use the environment:"
echo "  source venv/bin/activate"
echo "  python web_search_agent.py"
echo ""
echo "To run tests:"
echo "  pytest -v"