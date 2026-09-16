# syntax=docker/dockerfile:1
# Image admin-django (back-office Django).
# Contexte de build attendu : racine du monorepo (pour installer packages/domain).

FROM python:3.13-slim
WORKDIR /repo

# packages/domain d'abord (dépendance de admin-django, installée en editable) :
# couche de cache stable, indépendante du code Django lui-même.
COPY packages/domain ./packages/domain
COPY apps/admin-django/requirements.txt ./apps/admin-django/requirements.txt
# cd dans apps/admin-django avant l'install : `-e ../../packages/domain` dans
# requirements.txt est résolu par pip relativement au CWD, pas au fichier.
RUN cd apps/admin-django && pip install --no-cache-dir -r requirements.txt

COPY apps/admin-django ./apps/admin-django

RUN useradd --create-home --uid 1000 django \
 && chown -R django:django /repo
USER django
WORKDIR /repo/apps/admin-django

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=6 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health/', timeout=3)"

# runserver : suffisant pour la démo portfolio (mêmes secrets/paramètres de
# dev que le reste du projet) — pas un serveur de production.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec python manage.py runserver 0.0.0.0:8000"]
