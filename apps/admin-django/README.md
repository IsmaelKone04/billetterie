# admin-django

Back-office Django : gestion événements, organisateurs, plan de salle, staff.
Propriétaire du schéma Postgres (migrations).

**État : M1 — modèles noyau.** `Organizer`, `Venue`, `Section`, `Seat`,
`Event`, `TicketType` + admin basique (avec inlines). Pas encore de logique
d'achat/paiement (elle vivra côté `api-fastapi`, sur le même schéma).

## Lancer en local

```bash
cd apps/admin-django
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # .venv\Scripts\pip sous Windows
.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py createsuperuser
.venv/Scripts/python manage.py runserver
```

Nécessite Postgres démarré (`docker compose up -d postgres` à la racine du
repo) et un `.env` à la racine (ou dans ce dossier) — voir `.env.example`.
Admin sur `http://127.0.0.1:8000/admin/`.
