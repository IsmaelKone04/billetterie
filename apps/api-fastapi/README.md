# api-fastapi

API publique FastAPI : catalogue, panier, achat, webhook paiement, scan de
billet. Lit/écrit la base Postgres gérée par `admin-django` (Django reste
seul propriétaire du schéma et des migrations).

**État : Mn — achat, paiement Mobile Money, billets (QR signé + scan avec
sièges numérotés), marketplace multi-organisateurs (inscription + dashboard
analytics), vérifié de bout en bout via `docker compose up --build`.**

- `GET /events` — liste des événements publiés (statut `publie`), triés par
  date de début.
- `GET /events/{id}` — détail d'un événement publié (404 sinon), avec ses
  tarifs (`TicketType`).
- `POST /orders` — crée une commande (panier de tarifs), verrouille et
  réserve les billets (anti-survente via Redis + comptage en base). Pour un
  tarif lié à une section à places numérotées, attribue aussi un siège par
  billet (premier libre, jamais réutilisé tant que la commande qui le
  retient n'est pas échouée/annulée/remboursée ; 409 explicite si plus de
  sièges libres). Puis initie le paiement auprès du provider actif
  (`PAYMENT_PROVIDER`).
- `GET /orders/{transaction_id}/tickets?email=...` — « mes billets » :
  liste les billets d'une commande `billets_emis` (justificatif :
  `transaction_id` + e-mail acheteur), chacun avec un token QR signé.
- `POST /payments/webhook/{provider}` — webhook de paiement (`cinetpay` ou
  `simulator`) : vérifie la signature, appelle `check()` si le provider
  l'exige, déduplique, émet les billets (`Order.status → billets_emis`) ou
  marque la commande `echouee`.
- `POST /payments/simulate` — dev/tests uniquement (`PAYMENT_PROVIDER=simulator`) :
  déclenche un webhook auto-signé pour une commande donnée, sans dépendre
  d'un vrai opérateur Mobile Money.
- `POST /scan` — scan d'un billet à l'entrée (en-tête `X-Scan-Key`) : vérifie
  le token QR signé, marque le billet scanné, refuse tout second scan avec
  l'heure du premier.
- `POST /organizers/signup` — inscription organisateur en libre-service
  (mot de passe haché PBKDF2, jamais en clair en base), retourne un JWT.
- `POST /organizers/login` — authentification organisateur, retourne un JWT
  (`Authorization: Bearer ...`, valide 12h).
- `GET /organizers/me` — profil de l'organisateur authentifié.
- `GET /organizers/me/dashboard` — analytics par événement (billets vendus,
  taux de remplissage, revenus), pour les seuls événements de l'organisateur
  authentifié.
- `GET /health` — vérification de vie (pour le futur healthcheck Docker).

Voir `docs/RAPPORT.md` (entrées M3 à Mn) pour le détail des providers de
paiement, de la machine à états de la commande (`packages/domain`), du token
QR signé, de l'authentification organisateur (JWT, secret distinct de celui
des billets), de l'attribution des sièges numérotés, et des points ouverts
(pas de timeout automatique des commandes en attente de paiement, scan
protégé par une clé partagée plutôt qu'un compte staff individuel).

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
suppriment après chaque test (voir `tests/conftest.py`). 23 tests.
