# syntax=docker/dockerfile:1
# Image api-fastapi (API publique).
# Contexte de build attendu : racine du monorepo (pour installer packages/domain).

FROM python:3.13-slim
WORKDIR /repo

COPY packages/domain ./packages/domain
COPY apps/api-fastapi/requirements.txt ./apps/api-fastapi/requirements.txt
# cd dans apps/api-fastapi avant l'install : `-e ../../packages/domain` dans
# requirements.txt est résolu par pip relativement au CWD, pas au fichier.
RUN cd apps/api-fastapi && pip install --no-cache-dir -r requirements.txt

COPY apps/api-fastapi ./apps/api-fastapi

RUN useradd --create-home --uid 1000 fastapi \
 && chown -R fastapi:fastapi /repo
USER fastapi
WORKDIR /repo/apps/api-fastapi

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=6 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=3)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
