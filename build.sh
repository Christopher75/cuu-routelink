#!/usr/bin/env bash
# Render.com build script for CUU RouteLink
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
python manage.py seed_data
