web: python manage.py migrate && gunicorn config.wsgi:application --log-file - --timeout 60
worker: celery -A config worker --loglevel=info