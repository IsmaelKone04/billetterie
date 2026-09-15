# Rapport de progression — billetterie

Journal daté, mis à jour à chaque jalon. Ne duplique pas `git log` : décrit ce
qui a changé et pourquoi, les décisions prises, les points ouverts.

---

## 2026-09-15 — M0 : squelette du projet

Démarrage de la refonte totale du projet `Atelier-` (maquette Django de 2024,
achat simulé, sans paiement réel ni QR ni places numérotées). Décision : garder
uniquement la logique de résolution serveur du tarif à l'achat, reconstruire
le reste sur une architecture Django + FastAPI + Next.js.

**Fait :**
- Structure de dossiers créée (`apps/admin-django`, `apps/api-fastapi`,
  `apps/web`, `packages/domain`, `docker/`, `docs/`).
- `README.md` et `CLAUDE.md` initiaux rédigés.

**Décisions actées avec Ismaël :**
- Backend double : Django (back-office/admin, propriétaire du schéma
  Postgres) + FastAPI (API publique haute performance).
- Frontend Next.js découplé.
- Paiement Mobile Money via CinetPay (Orange Money/MTN/Moov/Wave), avec un
  provider `simulator` pour le développement (pas d'organisateurs réels à ce
  stade).
- Fonctionnalités prioritaires : scan de billets temps réel, places
  numérotées (plan de salle), marketplace multi-organisateurs, analytics
  organisateur.
- Nom retenu : **billetterie** (dépôt GitHub pas encore créé — à faire sur
  demande explicite).

**Backlog de fonctionnalités gratuites proposées (non engagées) :**
codes promo, liste d'attente automatique, export CSV participants, tableau de
bord "jour J" (scanné/vendu en temps réel), billets transférables,
notifications e-mail (confirmation + rappel J-1).

**Prochain jalon (M1) :** modèles Django noyau (`Organizer`, `Event`, `Venue`,
`SeatMap`, `TicketType`), migrations, admin basique, auth staff.

**Points ouverts :**
- Dépôt GitHub à créer (nom `billetterie`, privé) — sur demande explicite
  uniquement.
- Identifiants CinetPay réels non disponibles à ce stade — développement en
  mode `simulator` jusqu'à nouvel ordre.
