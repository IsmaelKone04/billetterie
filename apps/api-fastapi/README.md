# api-fastapi

API publique FastAPI : catalogue, panier, achat, webhook paiement, scan de
billet. Lit/écrit la base Postgres gérée par `admin-django` (Django reste
seul propriétaire du schéma et des migrations).

**État : M3 — achat et paiement Mobile Money.**

- `GET /events` — liste des événements publiés (statut `publie`), triés par
  date de début.
- `GET /events/{id}` — détail d'un événement publié (404 sinon), avec ses
  tarifs (`TicketType`).
- `POST /orders` — crée une commande (panier de tarifs), verrouille et
  réserve les billets (anti-survente via Redis + comptage en base), puis
  initie le paiement auprès du provider actif (`PAYMENT_PROVIDER`).
- `POST /payments/webhook/{provider}` — webhook de paiement (`cinetpay` ou
  `simulator`) : vérifie la signature, appelle `check()` si le provider
  l'exige, déduplique, émet les billets (`Order.status → billets_emis`) ou
  marque la commande `echouee`.
- `POST /payments/simulate` — dev/tests uniquement (`PAYMENT_PROVIDER=simulator`) :
  déclenche un webhook auto-signé pour une commande donnée, sans dépendre
  d'un vrai opérateur Mobile Money.
- `GET /health` — vérification de vie (pour le futur healthcheck Docker).

Voir `docs/RAPPORT.md` (entrée M3) pour le détail des providers de paiement,
de la machine à états de la commande (`packages/domain`) et des points
ouverts (pas d'assignation de sièges numérotés, pas de timeout automatique
des commandes en attente de paiement).

## Lancer en local

```bash
cd apps/api-fastapi
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # .venv\Scripts\pip sous Windows
.venv/Scripts/uvicorn app.main:app --reload --port 8000
```

Nécessite Postgres **et** Redis démarrés (`docker compose up -d postgres
redis` à la racine du repo) et un `.env` à la racine (ou dans ce dossier)
avec les variables `POSTGRES_*`, `REDIS_*` et `PAYMENT_PROVIDER` — voir
`.env.example`. `requirements.txt` installe aussi `packages/domain` en
editable (`-e ../../packages/domain`).

## Tests

```bash
.venv/Scripts/pytest
```

Tests d'intégration contre le vrai Postgres et le vrai Redis partagés avec
`admin-django` : insèrent des données de test en SQL brut puis les
suppriment après chaque test (voir `tests/conftest.py`).

**Pas encore fait :** génération de QR signé (au-delà du `qr_secret` brut),
page « mes billets », endpoint de scan, assignation de sièges numérotés —
jalon M4.
