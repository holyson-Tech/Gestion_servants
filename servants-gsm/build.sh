#!/usr/bin/env bash
# Exécuté par Render à chaque déploiement
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
python manage.py seed
# Crée l'administrateur la première fois (variables DJANGO_SUPERUSER_*), ignoré ensuite
python manage.py createsuperuser --noinput || true
