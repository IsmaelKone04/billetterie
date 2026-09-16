# admin-django

Back-office Django : gestion événements, organisateurs, plan de salle, staff.
Propriétaire du schéma Postgres (migrations).

**État : Mn — modèles noyau + achat/paiement + marketplace, sièges
numérotés attribués côté `api-fastapi`.** `Organizer`, `Venue`, `Section`,
`Seat`, `Event`, `TicketType`, `Order`, `Ticket`, `PaymentEvent` + admin
(avec inlines ; `PaymentEvent` en lecture seule, c'est un journal d'audit).
La logique d'achat/paiement (verrouillage, attribution des sièges, appels
CinetPay, webhooks) et l'inscription/authentification organisateur + le
dashboard analytics vivent côté `api-fastapi`, sur ce même schéma — Django
ne fait qu'exposer les données pour le back-office (et gérer le plan de
salle : `Section.has_numbered_seats` + `Seat` via l'admin).

Depuis M5, `Organizer` porte son propre `email`/`password_hash` (inscription
en libre-service via `api-fastapi`, hors du système d'auth Django) ; `user`
(compte Django staff) est désormais optionnel, réservé à un éventuel accès
admin manuel.

Thème visuel personnalisé (`static/admin/css/custom_theme.css` +
`templates/admin/base_site.html`) : palette neutre/indigo, cartes
arrondies, ombres douces — surcharge des variables CSS natives de l'admin
Django, mode sombre compris. Voir `docs/RAPPORT.md`.

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

Ou via Docker (voir `docker/admin.Dockerfile` et le service `admin-django`
de `docker-compose.yml` à la racine) : `docker compose up --build
admin-django`.
