#!/bin/bash
set -e

echo "🧪 Setting up Lab Data Simulator Environment with Pixi..."

if ! command -v pixi &> /dev/null; then
    echo "Pixi could not be found. Please install it first:"
    echo "  curl -fsSL https://pixi.sh/install.sh | bash"
    exit 1
fi

pixi install

echo ""
echo "✅ Setup Complete!"
echo "To run the demo, use:"
echo "  pixi run demo"
echo ""
echo "To enter the shell, use:"
echo "  pixi shell"
