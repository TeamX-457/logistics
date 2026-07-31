FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=logistica_tracking.settings.production

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# collectstatic only reads STATIC_ROOT/STATICFILES_DIRS and writes files —
# it never touches the database or Redis. production.py still requires
# DJANGO_SECRET_KEY/DB_*/REDIS_URL to exist at settings-import time, so we
# supply throwaway values scoped to this one build step only. Real values
# are supplied at container-run time (docker-compose env_file / platform
# env config) and are never baked into the image.
RUN SECRET_KEY=build-time-placeholder \
    DB_NAME=build DB_USER=build DB_PASSWORD=build DB_HOST=build DB_PORT=5432 \
    REDIS_URL=redis://build:6379/0 \
    python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "logistica_tracking.asgi:application"]
