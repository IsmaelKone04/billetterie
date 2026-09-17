# billetterie

Billetterie d'événements moderne pour le marché ivoirien — places numérotées,
scan de billets en temps réel, marketplace multi-organisateurs, analytics,
paiement Mobile Money (CinetPay : Orange Money / MTN / Moov / Wave).

> **État actuel : Mn.** Back-office Django avec modèles noyau (organisateurs,
> lieux, plan de salle, événements, tarifs, commandes, billets), API FastAPI
> (catalogue, achat, paiement Mobile Money, billets/QR avec **sièges
> numérotés attribués automatiquement**, scan, marketplace multi-
> organisateurs par JWT, dashboard analytics) et frontend Next.js complet
> (catalogue, achat, « mes billets », scan par caméra, inscription/
> connexion/dashboard organisateur), le tout vérifié de bout en bout via
> `docker compose up --build` (5 services). Reste ouvert : capture caméra
> non testée avec un vrai navigateur, pas de timeout automatique des
> commandes en attente, CinetPay jamais testé en conditions réelles — voir
> `docs/RAPPORT.md`. Ce README est mis à jour à chaque jalon.

## Stack

- **Back-office** : Django (Postgres, admin, gestion événements/organisateurs)
- **API publique** : FastAPI (catalogue, achat, paiement, scan)
- **Frontend** : Next.js
- **Infra** : Postgres, Redis, Docker Compose

## Structure

```
apps/
  admin-django/     # back-office
  api-fastapi/       # API publique
  web/               # frontend Next.js
packages/
  domain/            # schémas et logique partagés
docker/
docs/RAPPORT.md      # journal de progression
```

## Lancer le projet

**Stack complète** (Postgres, Redis, admin-django, api-fastapi, web) :

```bash
cp .env.example .env   # renseigner les secrets (voir commentaires du fichier)
docker compose up --build
```

Ports publiés sur l'hôte : admin-django `8000`, api-fastapi `8010` (décalé,
8000 déjà pris par Django), web `3000`, Postgres `5433`, Redis `6380`
(décalés pour cohabiter avec le projet `monbail` sur cette machine).

Pour ne lancer que l'infra (dev local des apps hors Docker, voir le README
de chaque app) :

```bash
docker compose up -d postgres redis
```

**Back-office Django** (`apps/admin-django/`) : voir son README.
**API publique FastAPI** (`apps/api-fastapi/`) : voir son README.
**Frontend Next.js** (`apps/web/`) : voir son README.

## Comptes de test (environnement local uniquement)

| Interface | URL | Identifiant | Mot de passe |
| --- | --- | --- | --- |
| Admin Django | http://localhost:8000/admin/ | `admin` | `BilletterieDemo2026!` |

Compte superuser Django, local à cette machine de développement — jamais
utilisé en production, pas de données sensibles réelles derrière. À
régénérer (`docker compose exec admin-django python manage.py
changepassword admin`) si ce dépôt devient public ou si l'environnement
est exposé au-delà de la machine locale.

## Roadmap

Voir `docs/RAPPORT.md` pour le détail des jalons M0 à Mn.
