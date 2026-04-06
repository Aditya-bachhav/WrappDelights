#!/usr/bin/env bash
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Entering Django project directory..."
cd delights_backend/core

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build complete. Data migrations will run in startCommand."