#!/usr/bin/env bash
# Render.com build script
set -o errexit

# libmagic needed by python-magic for MIME type detection
apt-get update && apt-get install -y --no-install-recommends libmagic1 || true

pip install -r requirements/base.txt

python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py update_site
python manage.py seed_demo_data
