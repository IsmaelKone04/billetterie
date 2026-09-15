# CLAUDE.md — billetterie

Ce fichier guide toute session Claude Code travaillant sur ce dépôt. Langue du
projet et des échanges : **français**.

---

## 1. Ce qu'est le projet

Billetterie d'événements moderne pour le marché ivoirien (Côte d'Ivoire),
pensée comme une alternative plus performante et plus riche en
fonctionnalités qu'une billetterie classique (Tickerama et équivalents).

Refonte totale du projet `Atelier-` (2024, maquette Django simple, achat
simulé sans paiement réel, aucun QR, aucune place numérotée) — seule la
logique de résolution serveur du tarif à l'achat est reprise conceptuellement,
tout le reste est reconstruit.

## 2. Architecture

```
apps/
  admin-django/     # back-office : événements, organisateurs, staff, plan de salle
  api-fastapi/       # API publique : catalogue, achat, paiement, scan billet
  web/               # Next.js — vitrine, achat, dashboard organisateur
packages/
  domain/            # schémas partagés + machine à états achat/billet
docker/
docker-compose.yml
docs/RAPPORT.md      # journal de progression, mis à jour à chaque jalon
```

- **Django** est propriétaire du schéma Postgres (migrations). Back-office
  uniquement (staff, organisateurs, gestion événements/plan de salle).
- **FastAPI** lit/écrit la même base. API publique haute performance :
  catalogue, panier, achat, webhook paiement, scan de billet.
- **Next.js** ne parle qu'aux API REST — jamais de connexion DB directe.
- **Redis** : verrouillage anti-survente à l'achat + file de tâches
  (QR, e-mail).
- **Postgres** : base unique partagée Django/FastAPI.

## 3. Paiement — Mobile Money

Agrégateur **CinetPay** (Orange Money / MTN MoMo / Moov Money / Wave derrière
un seul contrat). Flux : `POST /v2/payment` → redirection → webhook (HMAC
vérifié, anti-rejeu) → confirmation systématique via `POST /v2/payment/check`
avant d'émettre les billets. Jamais de confiance aveugle au webhook seul.

Un provider `simulator` existe pour le développement local : permet de
dérouler tout le flux achat → paiement → émission de billets sans
identifiants CinetPay réels.

## 4. Conventions de travail

- **Français** pour tout le contenu visible, les commits, et `docs/RAPPORT.md`.
- Travailler **par jalons validés** (voir `docs/RAPPORT.md` pour la liste) :
  proposer le changement, montrer le diff, attendre le feu vert avant
  d'enchaîner.
- **`docs/RAPPORT.md` à jour à chaque jalon** — daté, ce qui a changé et
  pourquoi, sans dupliquer `git log`.
- **`README.md` à jour** à chaque changement structurel, pas seulement à la
  fin.
- Ne jamais committer de secret. `.env` reste local, `.env.example` documente
  chaque variable.
- **Ne jamais créer de dépôt GitHub ni pousser sans demande explicite.**
- Golden rule : ne rien affirmer de fonctionnel qui ne l'est pas encore (ex.
  ne pas dire "paiement Mobile Money actif" tant que seul le simulateur
  tourne).
- Une fois le projet présentable (`docker compose up --build` fonctionnel de
  bout en bout), proposer son ajout au portfolio
  (`c:\Portfolio\frontend\src\data\mockData.js`) — diff soumis avant tout
  commit dans le dépôt Portfolio, conformément à son propre `CLAUDE.md`.

## 5. Identité Git

Tous les commits sous l'identité personnelle `IsmaelKone04`
(`user.name = Ismaël koné`, adresse `noreply` GitHub personnelle) — jamais
une adresse professionnelle.
