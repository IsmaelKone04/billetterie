# api-fastapi

API publique FastAPI : catalogue, panier, achat, webhook paiement, scan de
billet. Lit/écrit la base Postgres gérée par `admin-django` (Django reste
seul propriétaire du schéma et des migrations).

**État : M2 — catalogue public en lecture seule.**

- `GET /events` — liste des événements publiés (statut `publie`), triés par
  date de début.
- `GET /events/{id}` — détail d'un événement publié (404 sinon), avec ses
  tarifs (`TicketType`).
- `GET /health` — vérification de vie (pour le futur healthcheck Docker).

## Lancer en local

```bash
cd apps/api-fastapi
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # .venv\Scripts\pip sous Windows
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

Nécessite Postgres démarré (`docker compose up -d postgres` à la racine du
repo) et un `.env` à la racine (ou dans ce dossier) avec les variables
`POSTGRES_*` — voir `.env.example`.

## Tests

```bash
.venv/Scripts/pytest
```

Tests d'intégration contre le vrai Postgres partagé avec `admin-django` :
insèrent des données de test en SQL brut puis les suppriment après chaque
test (voir `tests/conftest.py`).

**Pas encore fait :** achat/paiement, billets/QR, scan — jalons M3/M4.
