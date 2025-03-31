#!/bin/bash
set -e

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements-dev.txt


echo "Installing pre-commit hooks..."
pre-commit install

echo "Setup complete! Virtual environment is activated."
echo "Run 'deactivate' to exit the virtual environment when you're done."

if [ -z "$DJANGO_DEBUG" ]; then
    echo "You'll need to add enviorment variables to your shell profile. venv/bin/activate is a good place to do this."
fi
