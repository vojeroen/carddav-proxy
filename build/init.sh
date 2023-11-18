#!/usr/bin/env bash

cd /app || exit
#alembic upgrade head
gunicorn --workers=4 --bind=0.0.0.0:8000 app:app
