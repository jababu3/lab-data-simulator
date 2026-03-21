#!/bin/bash
set -e

echo "🧪 Setting up Lab Data Simulator Environment with Poetry..."

# Ensure poetry is installed (we know it is, but good check)
if ! command -v poetry &> /dev/null; then
    echo "Poetry could not be found. Please install it first."
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
poetry install

echo ""
echo "✅ Setup Complete!"
echo "To run the demo, use:"
echo "poetry run python examples/demo_simulation.py"
echo ""
echo "To enter the shell, use:"
echo "poetry shell"
