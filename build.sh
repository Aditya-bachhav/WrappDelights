#!/usr/bin/env bash
set -o errexit

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Entering Django project directory..."
cd delights_backend/core

echo "Running database migrations..."
python manage.py migrate

echo "Creating superuser with hardcoded credentials..."
python manage.py ensure_superuser

echo "Collecting static files..."
python manage.py collectstatic --noinput