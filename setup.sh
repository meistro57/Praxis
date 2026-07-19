#!/usr/bin/env bash

# Setup Script for Praxis Repository
# Configures local directory pathways, verifies virtual environments, and ensures dependencies are correct.

set -euo pipefail

echo "===================================================="
echo "Initializing Praxis local development environment..."
echo "===================================================="

# Determine project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${PROJECT_ROOT}"

# Create directories
echo "Creating required folders..."
mkdir -p data logs prompts

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed." >&2
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "System Python version: ${PYTHON_VERSION}"

# Check virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
# shellcheck disable=SC1091
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
if [ -f "requirements-dev.txt" ]; then
    echo "Installing dev dependencies..."
    pip install -r requirements-dev.txt
elif [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "Warning: Neither requirements.txt nor requirements-dev.txt found."
fi

# Set up local .env
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
    else
        echo "Warning: No .env.example found. Creating a blank .env..."
        touch .env
    fi
fi

echo "===================================================="
echo "Praxis environment successfully initialized!"
echo "To activate the environment: source .venv/bin/activate"
echo "To run the tests: python -m pytest"
echo "To run the CLI: python run.py --help"
echo "===================================================="
