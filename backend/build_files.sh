#!/bin/bash
# Build step run by Vercel's @vercel/static-build. It installs dependencies and
# collects static assets into staticfiles/, which Vercel serves from its CDN.
set -e

python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --noinput
