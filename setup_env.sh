#!/bin/bash
set -e

echo "🧪 Setting up Lab Data Simulator Environment with Pixi..."

# Ensure pixi is installed
if ! command -v pixi &> /dev/null; then
    echo "Pixi could not be found. Please install it first: curl -fsSL https://pixi.sh/install.sh | bash"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
pixi install

echo ""
echo "✅ Setup Complete!"
echo "To run the demo, use:"
echo "pixi run python examples/demo_simulation.py"
echo ""
echo "To enter the shell, use:"
echo "pixi shell"
