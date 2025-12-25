#!/bin/bash
# Run Django REST Framework benchmark server
# Port: 8005

cd "$(dirname "$0")"

echo "Starting Django REST Framework on port 8005..."
exec uvicorn django_project.asgi:application --host 0.0.0.0 --port 8005 --workers 1 --no-access-log
