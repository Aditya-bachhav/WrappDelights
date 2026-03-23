#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python delights_backend/core/manage.py collectstatic --noinput
python delights_backend/core/manage.py migrate