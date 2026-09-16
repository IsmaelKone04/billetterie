# billetterie

Billetterie d'événements moderne pour le marché ivoirien — places numérotées,
scan de billets en temps réel, marketplace multi-organisateurs, analytics,
paiement Mobile Money (CinetPay : Orange Money / MTN / Moov / Wave).

> **État actuel : M6.** Back-office Django avec modèles noyau (organisateurs,
> lieux, plan de salle, événements, tarifs, commandes, billets), API FastAPI
> (catalogue, achat, paiement Mobile Money, billets/QR, scan, marketplace
> multi-organisateurs par JWT, dashboard analytics) et **frontend Next.js
> complet** (catalogue, achat, « mes billets », scan par caméra,
> inscription/connexion/dashboard organisateur), branché sur l'API FastAPI.
> Reste à faire : assignation de sièges numérotés, vérification Docker
> Compose de bout en bout, avant intégration au portfolio. Ce README est mis
> à jour à chaque jalon (voir `docs/RAPPORT.md`).

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
**Frontend Next.js** (`apps/web/`) : voir son README.

## Roadmap

Voir `docs/RAPPORT.md` pour le détail des jalons M0 à Mn.
