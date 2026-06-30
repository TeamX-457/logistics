"""Vercel serverless entry point.

Vercel's @vercel/python runtime imports the module-level ``app`` callable and
serves it as a WSGI application.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = get_wsgi_application()
