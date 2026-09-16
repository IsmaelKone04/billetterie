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
- Identifiants CinetPay réels non disponibles à ce stade — développement en
  mode `simulator` jusqu'à nouvel ordre.

---

## 2026-09-15 — Dépôt GitHub créé

Dépôt privé **github.com/IsmaelKone04/billetterie** créé et le commit M0
poussé (branche `master`).

## 2026-09-15 — M1 : modèles Django noyau

**Fait :**
- Projet Django scaffoldé dans `apps/admin-django/` (Django 6.1.1, config
  `config/`, app `ticketing/`).
- `settings.py` durci sur le même modèle qu'Atelier- : `.env` obligatoire
  hors `DEBUG`, `SECRET_KEY` requise en production, `LANGUAGE_CODE=fr-fr`,
  `TIME_ZONE=Africa/Abidjan`, base Postgres (plus de SQLite).
- Modèles noyau créés (`ticketing/models.py`) : `Organizer` (compte
  organisateur pour la marketplace multi-organisateurs), `Venue`, `Section`
  (zone du plan de salle, numérotée ou à capacité libre), `Seat` (siège
  numéroté), `Event` (statuts brouillon/publié/terminé/annulé), `TicketType`
  (remplace le dict `TARIFS` codé en dur de l'ancienne maquette — prix,
  quota, fenêtre de vente, rattachable à une `Section`).
- Admin Django basique enregistré (`ticketing/admin.py`) avec inlines
  (sièges dans une section, tarifs dans un événement).
- Migration `0001_initial` générée puis appliquée avec succès contre un vrai
  Postgres (conteneur Docker).
- Superuser de test créé, `manage.py runserver` vérifié : `/` → 200,
  `/admin/login/` → 200, les 5 modèles top-niveau bien enregistrés dans
  l'admin.

**Incident résolu en cours de route :** Docker Desktop bloqué (moteur
WSL2 ne répondant plus) — résolu par `wsl --shutdown` puis relance complète
de Docker Desktop (a aussi redémarré les conteneurs `monbail` déjà en
cours, qui tournent en parallèle sur cette machine — pas de perte).
Conséquence durable : les ports hôte de `postgres`/`redis` dans
`docker-compose.yml` sont décalés (`5433`/`6380` au lieu de `5432`/`6379`)
car `monbail` occupe déjà les ports par défaut sur cette machine — contrôlé
via `POSTGRES_PORT`/`REDIS_PORT` dans `.env`.

**Prochain jalon (M2) :** FastAPI — catalogue public en lecture seule sur la
même base Postgres.

---

## 2026-09-15 — M2 : FastAPI, catalogue public en lecture seule

**Fait :**
- Projet FastAPI scaffoldé dans `apps/api-fastapi/` (FastAPI 0.141.1,
  SQLAlchemy 2.0 async + asyncpg, `app/`).
- Modèles SQLAlchemy en lecture seule (`app/models.py`) reflétant exactement
  le schéma créé par Django (`ticketing_organizer`, `ticketing_venue`,
  `ticketing_event`, `ticketing_tickettype`, vérifié via `\d` sur le vrai
  Postgres) — FastAPI ne crée ni ne modifie jamais de table, Django reste
  seul propriétaire des migrations.
- Endpoints : `GET /events` (liste des événements au statut `publie`,
  triés par date), `GET /events/{id}` (détail + tarifs, 404 si absent ou non
  publié), `GET /health`.
- Suite de tests d'intégration (`pytest` + `httpx.AsyncClient`, 5 tests)
  contre le **vrai** Postgres partagé avec `admin-django` : insertion de
  données de test en SQL brut puis nettoyage systématique après chaque test
  (aucune pollution laissée en base — vérifié par comptage après coup).
  Couvre : filtrage brouillon/publié, 404 sur événement inconnu ou non
  publié, contenu du détail (lieu, tarifs).
- Vérification manuelle : `uvicorn` lancé en local, `/health` → 200,
  `/events` → `[]` (base de dev vide, aucun événement réel créé), `/events/1`
  → 404.

**Décision technique :** pas de dépendance croisée avec le code Django (pas
d'import du modèle Django) — FastAPI redéfinit son propre mapping
SQLAlchemy vers les mêmes tables. Si le schéma Django change, il faudra
répercuter le changement ici manuellement (accepté pour l'instant, à
surveiller si ça devient source de bugs).

**Prochain jalon (M3) :** achat — `Order`/`Ticket`, verrouillage Redis
anti-survente, intégration CinetPay + provider `simulator`, webhook +
vérification systématique.
