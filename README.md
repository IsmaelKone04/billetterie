# billetterie

Billetterie d'événements moderne pour le marché ivoirien — places numérotées,
scan de billets en temps réel, marketplace multi-organisateurs, analytics,
paiement Mobile Money (CinetPay : Orange Money / MTN / Moov / Wave).

> **État actuel : M4.** Back-office Django avec modèles noyau (organisateurs,
> lieux, plan de salle, événements, tarifs, commandes, billets) et API
> FastAPI avec catalogue public + achat + paiement Mobile Money (CinetPay +
> provider `simulator`) + billets (QR signé, page « mes billets », scan
> anti-duplication). Pas encore de marketplace multi-organisateurs, de
> dashboard analytics, ni de frontend (les pages « mes billets »/scan
> existent comme endpoints API, pas encore comme pages Next.js — prévu au
> jalon M6). Ce README est mis à jour à chaque jalon (voir `docs/RAPPORT.md`).

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

Infra partagée (Postgres/Redis, ports décalés à 5433/6380 pour cohabiter
avec le projet `monbail` sur cette machine) :

```bash
docker compose up -d postgres redis
```

**Back-office Django** (`apps/admin-django/`) : voir son README.
**API publique FastAPI** (`apps/api-fastapi/`) : voir son README.

Frontend Next.js pas encore commencé (jalon M6).

## Roadmap

Voir `docs/RAPPORT.md` pour le détail des jalons M0 à Mn.
