web: daphne -b 0.0.0.0 -p $PORT logistica_tracking.asgi:application
worker: celery -A logistica_tracking worker --loglevel=info
