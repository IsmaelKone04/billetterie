# admin-django

Back-office Django : gestion événements, organisateurs, plan de salle, staff.
Propriétaire du schéma Postgres (migrations).

**État : M5 — modèles noyau + achat/paiement + marketplace.** `Organizer`,
`Venue`, `Section`, `Seat`, `Event`, `TicketType`, `Order`, `Ticket`,
`PaymentEvent` + admin (avec inlines ; `PaymentEvent` en lecture seule, c'est
un journal d'audit). La logique d'achat/paiement (verrouillage, appels
CinetPay, webhooks) et désormais l'inscription/authentification organisateur
+ le dashboard analytics vivent côté `api-fastapi`, sur ce même schéma —
Django ne fait qu'exposer les données pour le back-office.

Depuis M5, `Organizer` porte son propre `email`/`password_hash` (inscription
en libre-service via `api-fastapi`, hors du système d'auth Django) ; `user`
(compte Django staff) est désormais optionnel, réservé à un éventuel accès
admin manuel.

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
