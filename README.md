# billetterie

Billetterie d'événements moderne pour le marché ivoirien — places numérotées,
scan de billets en temps réel, marketplace multi-organisateurs, analytics,
paiement Mobile Money (CinetPay : Orange Money / MTN / Moov / Wave).

> **État actuel : M0 — squelette du projet.** Aucune fonctionnalité n'est
> encore implémentée. Ce README sera mis à jour à chaque jalon (voir
> `docs/RAPPORT.md`).

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

À compléter au fur et à mesure des jalons (voir `docs/RAPPORT.md`). Pour
l'instant, aucun service n'est fonctionnel.

## Roadmap

Voir `docs/RAPPORT.md` pour le détail des jalons M0 à Mn.
