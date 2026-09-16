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

---

## 2026-09-16 — M3 : achat, verrouillage Redis, paiement Mobile Money

**Fait :**
- Nouveau package partagé `packages/domain` (`domain/order_state_machine.py`) :
  machine à états de la commande (`OrderStatus`, `ORDER_TRANSITIONS`,
  `verifier_transition()`), pattern porté de monbail
  (`escrow-state-machine.ts`). Installé en editable (`pip install -e`) dans
  les venvs `admin-django` et `api-fastapi` — les deux étant en Python, pas
  besoin de dupliquer le graphe de transitions comme monbail devait le faire
  entre TypeScript (Next.js/Nest) et son domaine partagé.
- Modèles Django ajoutés (`ticketing/models.py`, migration `0002`) : `Order`
  (commande publique, sans compte utilisateur requis — email/téléphone),
  `Ticket` (un par place, `qr_secret` unique généré côté application),
  `PaymentEvent` (audit de chaque webhook reçu, lecture seule dans l'admin).
  Admin enregistré avec inlines (billets dans une commande).
- Côté `api-fastapi`, modèles SQLAlchemy miroir (désormais en **lecture ET
  écriture** pour `Order`/`Ticket`/`PaymentEvent`, toujours en lecture seule
  pour le catalogue) : ajout de `type_annotation_map` sur `Base` pour mapper
  `datetime` → `TIMESTAMP WITH TIME ZONE` (sans quoi asyncpg refuse les
  datetimes timezone-aware qu'on écrit).
- Verrouillage Redis anti-survente (`app/services/locks.py`) : verrou court
  (`SET NX EX`, TTL 10 s) par tarif (`ticket_type_id`), acquis dans un ordre
  trié pour plusieurs tarifs à la fois (pas d'interblocage). Le contrôle de
  quota définitif reste fait en base (comptage des billets déjà réservés par
  des commandes non `echouee`/`annulee`) — Redis sert de point de
  sérialisation rapide, pas de source de vérité du stock (pattern
  d'idempotence repris de monbail, `redis-py` async au lieu d'`ioredis`).
- `POST /orders` (`api-fastapi`) : valide le panier, verrouille, réserve les
  billets **immédiatement** (créés dès la commande, avant paiement — c'est
  ce qui retient le stock pendant la fenêtre de paiement), puis appelle le
  provider de paiement actif.
- Deux providers de paiement (`app/payments/`), interface commune
  `PaymentProvider` :
  - `CinetPayProvider` : `POST /v2/payment` (arrondi du montant XOF au
    multiple de 5), webhook `notify_url` (HMAC-SHA256 de 16 champs `cpm_*`
    concaténés dans l'ordre documenté, en-tête `x-token`), puis
    `POST /v2/payment/check` **systématique** avant toute émission de
    billets — jamais de confiance aveugle au webhook seul. Ordre des champs
    et logique repris tels quels de l'intégration monbail
    (`cinetpay.provider.ts`), déjà éprouvée sur ce marché. Lève une erreur
    explicite si les identifiants CinetPay ne sont pas configurés (pas de
    simulation silencieuse).
  - `SimulatorProvider` : webhook auto-signé HMAC (secret dev dédié,
    `SIMULATOR_SECRET`, sans rapport avec CinetPay) ; `requires_check =
    False` car il n'y a pas de système externe distinct à interroger — le
    webhook auto-signé est la seule source de vérité. Déclenchable via
    `POST /payments/simulate` (dev/tests uniquement, actif seulement si
    `PAYMENT_PROVIDER=simulator`).
- `POST /payments/webhook/{provider}` : point d'entrée commun aux deux
  providers — vérifie la signature, appelle `check()` si le provider l'exige,
  déduplique par `provider_event_id` (`PaymentEvent` unique en base, pattern
  repris de monbail), applique la transition d'état (`PAIEMENT_EN_ATTENTE` →
  `PAYEE` → `BILLETS_EMIS`, ou → `ECHOUEE`) via la machine à états partagée.
- 11 tests d'intégration (6 catalogue + 5 achat/paiement) contre le vrai
  Postgres et le vrai Redis partagés avec `admin-django` : réservation de
  quota, refus si quota dépassé, événement inconnu, paiement réussi (émission
  des billets), paiement échoué, rejet de signature invalide,
  **idempotence** du webhook (rejouer la même notification ne ré-applique
  rien). Nettoyage systématique après chaque test — vérifié par comptage
  après coup (0 ligne restante sur les 7 tables concernées).
- Vérification manuelle de bout en bout avec un **vrai serveur `uvicorn`** et
  un **vrai webhook HTTP signé** (pas seulement le raccourci de test
  `/payments/simulate`) : événement créé via `manage.py shell` (Django),
  `POST /orders` (réservation de 2 billets), `POST /payments/webhook/simulator`
  avec une signature HMAC calculée manuellement en Python — commande passée à
  `billets_emis`, 2 billets `valide` avec QR secrets uniques, `PaymentEvent`
  journalisé. Données de test nettoyées après coup (vérifié).

**Décisions techniques :**
- Les billets sont créés **dès la réservation** (avant paiement confirmé),
  pas seulement à l'émission — c'est ce qui protège le quota pendant la
  fenêtre de paiement. Une commande `echouee`/`annulee` libère implicitement
  le quota (exclue du comptage des billets « réservés »). Pas de timeout
  automatique de libération des commandes `paiement_en_attente` restées
  bloquées — **point ouvert**, à traiter avant un usage en production (tâche
  planifiée ou TTL).
- Places numérotées (`Seat`) non gérées à ce stade : tous les billets sont
  créés avec `seat_id = NULL`, quel que soit le tarif. L'assignation de
  sièges spécifiques pour les sections à places numérotées reste à faire
  (probablement au jalon frontend, M6, où la sélection de siège a du sens
  côté UI) — **point ouvert**, non implémenté, signalé plutôt qu'ignoré.
- Identifiants CinetPay réels toujours indisponibles → `CinetPayProvider`
  n'a été vérifié que par lecture de code et cohérence avec l'intégration
  monbail, **pas par un appel réel à l'API CinetPay**. À tester dès que des
  identifiants seront disponibles.

## 2026-09-16 — M4 : billets, QR signé, scan anti-duplication

**Construit et vérifié :**
- `app/services/qr.py` : token QR = HMAC-SHA256 de `(ticket_id, qr_secret)`
  signé avec `JWT_SECRET`, jamais `qr_secret` en clair — même si le token QR
  fuite, il ne révèle pas le secret, et sans `JWT_SECRET` il est impossible
  d'en fabriquer un nouveau pour un autre `ticket_id`. Rien de plus n'est
  stocké en base : génération et vérification recalculent toujours le HMAC.
- `GET /orders/{transaction_id}/tickets?email=...` (« mes billets ») : pas de
  compte acheteur, la connaissance du `transaction_id` (reçu à l'achat) +
  l'e-mail sert de justificatif — comme un lien de confirmation de commande
  classique. Renvoie 409 si la commande n'est pas encore `billets_emis`.
- `POST /scan` : vérifie le token QR (signature + billet appartenant à une
  commande `billets_emis` + pas déjà annulé), marque le billet `scanne`,
  refuse tout second scan avec l'heure du premier (409, anti-duplication).
  Protégé par un en-tête `X-Scan-Key` (clé partagée `SCAN_API_KEY`) — voir
  point ouvert ci-dessous.
- `API_DEBUG` (FastAPI) introduit sur le même modèle que `DJANGO_DEBUG` :
  `JWT_SECRET`/`SCAN_API_KEY` n'ont un secret de dev par défaut que si
  `API_DEBUG=true` ; sinon un secret manquant fait échouer explicitement les
  endpoints concernés (503) plutôt que de tourner avec un secret devinable.
- 5 nouveaux tests d'intégration (« mes billets » avec e-mail correct/incorrect,
  commande pas encore émise, scan accepté puis refusé en double, mauvaise clé
  de scan, token falsifié) contre le vrai Postgres/Redis — 16 tests au total,
  tous verts. Vérification manuelle de bout en bout avec un **vrai serveur
  `uvicorn`** et de **vrais appels HTTP** (achat → paiement simulé → « mes
  billets » → scan deux fois → mauvaise clé → token falsifié), chaque cas
  observé avec le bon code HTTP. Données de test nettoyées après coup,
  vérifié par comptage (0 ligne restante sur les 7 tables concernées).

**Décisions techniques :**
- Portée volontairement limitée au **backend** : `apps/web/` (Next.js) n'a
  pas encore démarré (prévu au jalon M6). La « page mes billets » et
  l'« écran de scan » du plan initial sont donc, à ce stade, des **endpoints
  API** (`GET .../tickets`, `POST /scan`) exploitables par n'importe quel
  client HTTP — les pages Next.js elles-mêmes (affichage du QR, caméra via
  `getUserMedia`) sont reportées à M6, pour éviter de construire un
  frontend partiel maintenant puis de le refaire à M6. Signalé plutôt que
  fait à moitié.
- Le scan est protégé par une **clé partagée** (`SCAN_API_KEY`, en-tête
  `X-Scan-Key`), pas par un compte staff individuel — `Ticket.scanned_by`
  reste `NULL` dans tous les cas. Un vrai système d'authentification staff
  (identifier *qui* a scanné) demanderait de connecter l'API FastAPI aux
  utilisateurs Django (`auth_user`), ce qui est hors du périmètre initial de
  ce jalon — **point ouvert**, signalé plutôt qu'ignoré.
- Le token QR encode le HMAC de `(ticket_id, qr_secret)` plutôt que
  `qr_secret` seul : ça permet un lookup direct par `ticket_id` (clé
  primaire indexée) côté scan, sans dépendre uniquement de l'index unique
  sur `qr_secret`, et ça garde `qr_secret` hors du QR lui-même (défense en
  profondeur si le token QR fuite par un autre canal que le scan prévu).
- Pas de génération d'image QR côté backend (aucune dépendance ajoutée) : le
  backend ne produit que le *token* signé ; l'encodage en image QR revient
  au frontend (Next.js, M6), qui a la bibliothèque JS adaptée et un endroit
  où l'afficher.

**Prochain jalon (M5) :** marketplace multi-organisateurs — inscription
organisateur, dashboard analytics (ventes, remplissage, revenus).

## 2026-09-16 — M5 : marketplace multi-organisateurs, dashboard analytics

**Construit et vérifié :**
- Schéma `Organizer` (Django, migration `0003_organizer_selfservice_auth`) :
  ajout de `email` (unique) et `password_hash`, `user` (compte staff Django)
  devient **optionnel** — un organisateur auto-inscrit n'a pas forcément de
  compte Django, ce n'est pas le même système d'authentification.
- `app/services/auth.py` : hachage de mot de passe en PBKDF2-HMAC-SHA256
  (200 000 itérations, sel aléatoire, stdlib uniquement — aucune dépendance
  ajoutée pour ça) et JWT de session (`pyjwt`, `ORGANIZER_JWT_SECRET` —
  secret **distinct** de `JWT_SECRET` des billets, valable 12h).
- `app/services/analytics.py` : agrégations par événement (billets vendus,
  quota total, revenu) à partir de `Order`/`Ticket`/`TicketType`, un billet
  comptant comme vendu s'il appartient à une commande `billets_emis` et n'est
  pas annulé (même exclusion que le scan). Taux de remplissage protégé
  contre la division par zéro (événement sans aucun tarif → `0.0`).
- Nouveaux endpoints : `POST /organizers/signup`, `POST /organizers/login`,
  `GET /organizers/me`, `GET /organizers/me/dashboard` (protégés par
  `Authorization: Bearer <jwt>` sauf signup/login).
- 5 nouveaux tests d'intégration (inscription puis profil, e-mail déjà
  utilisé → 409, mot de passe incorrect → 401, accès sans token → 401,
  dashboard reflétant une vraie vente simulée avec le bon revenu/taux de
  remplissage) — 21 tests au total, tous verts.
- Vérification manuelle avec un **vrai serveur `uvicorn`** et de **vrais
  appels HTTP** : inscription → doublon rejeté (409) → mauvais mot de passe
  rejeté (401) → connexion correcte → `/me` sans/avec token → dashboard vide
  → achat + paiement simulé de 3 billets → dashboard reflétant exactement 3
  billets vendus, 9000 FCFA de revenu, 6 % de remplissage (3/50). Données de
  test (organisateur, lieu, événement, tarif, commande, billets) nettoyées
  après coup, vérifié par comptage (0 ligne restante).

**Décisions techniques :**
- **JWT via FastAPI plutôt que sessions Django**, tranché avec Ismaël avant
  de coder : un frontend Next.js découplé (M6) qui appelle déjà FastAPI pour
  tout le reste (catalogue, achat, scan) n'a besoin que d'un seul client HTTP
  et d'un en-tête `Authorization`, sans gérer de cookies cross-origin vers
  Django. L'inscription/connexion et le dashboard analytics vivent donc
  entièrement côté `api-fastapi`, pas dans `admin-django`.
- Secret de signature JWT **distinct** entre billets (`JWT_SECRET`) et
  session organisateur (`ORGANIZER_JWT_SECRET`) : deux usages de signature
  différents ne doivent jamais partager la même clé, même si un compromis
  serait de gravité différente dans les deux cas.
- Mot de passe haché en PBKDF2 stdlib plutôt qu'une dépendance externe
  (bcrypt/passlib) : suffisant pour ce volume, cohérent avec le style déjà
  utilisé pour le HMAC des tokens QR (pas de dépendance ajoutée sans besoin).
- **Pas de limitation de débit sur `/organizers/login`** (brute force) —
  **point ouvert**, signalé plutôt qu'ignoré ; à traiter si le projet va vers
  une vraie mise en production (ex. limitation par IP/e-mail via Redis, déjà
  présent dans la stack pour le verrouillage anti-survente).
- Le dashboard reste un **endpoint JSON**, pas une page Next.js — même
  logique de portée que M4 : `apps/web/` n'a pas démarré, la page dashboard
  elle-même est reportée à M6.

**Prochain jalon (M6) :** frontend Next.js complet (catalogue, achat, « mes
billets », écran de scan caméra, inscription/connexion organisateur,
dashboard analytics) branché sur les API Django/FastAPI existantes.

## 2026-09-16 — M6 : frontend Next.js complet

**Construit et vérifié :**
- `apps/web/` scaffoldé avec `create-next-app` (Next.js 16.3.5, App Router,
  TypeScript, Tailwind CSS 4). Next.js 16 diffère significativement des
  versions antérieures (voir `node_modules/next/dist/docs/`, consulté avant
  d'écrire du code) — `params`/`searchParams` en promesses, `PageProps`/
  `LayoutProps` générés automatiquement, etc.
- Pages : `/` (catalogue, server component), `/evenements/[id]` (détail +
  formulaire d'achat), `/commande/[transactionId]` (statut de paiement,
  simulation en mode `simulator`, affichage des billets une fois émis),
  `/mes-billets` (recherche par transaction_id + e-mail), `/scan` (caméra
  `getUserMedia` + décodage `jsqr`, avec saisie manuelle du token en
  secours), `/organisateurs/inscription`, `/organisateurs/connexion`,
  `/organisateurs/tableau-de-bord` (analytics, protégé côté client par la
  présence d'un JWT en `localStorage`).
- `lib/api.ts` : client HTTP unique et typé vers `api-fastapi`, types
  TypeScript alignés sur les schémas Pydantic (aucune duplication de
  formats, juste retranscrits explicitement — pas de génération de client
  automatique pour ce volume d'endpoints).
- QR : encodage (`qrcode`) côté « mes billets »/commande, décodage (`jsqr`)
  côté scan — aucune image QR générée côté backend (cf. M4), tout se passe
  ici.
- **CORS ajouté côté `api-fastapi`** (`CORSMiddleware`, origines autorisées
  via `CORS_ALLOWED_ORIGINS`, `http://localhost:3000` par défaut) : le
  frontend appelle FastAPI directement depuis le navigateur, pas de proxy.
- Bug réel trouvé et corrigé en testant l'inscription organisateur depuis
  un serveur fraîchement relancé : le routeur `organizers` n'était pas
  enregistré dans le process `uvicorn` resté actif depuis M5 (pas de
  `--reload`) — leçon de procédure, pas un bug de code (toujours relancer
  proprement le serveur de vérification manuelle après un changement de
  `main.py`).
- `npm run build` et `npm run lint` systématiquement propres (0 erreur,
  0 warning) après correction d'un typage implicite et de plusieurs
  violations de la règle `react-hooks/set-state-in-effect` (nouvelle dans
  cette version — lecture de `localStorage`/`sessionStorage` après montage
  et fetch de données au montage, deux cas légitimes, documentés en ligne).
- Vérification de bout en bout **sans navigateur réel** (environnement
  CLI) : un vrai `uvicorn` + un vrai `next dev`, `curl` sur les pages
  server-rendues (catalogue, détail événement) confirmant le contenu
  attendu, puis tout le flux achat → paiement simulé → « mes billets » →
  scan → dashboard organisateur rejoué avec les **mêmes requêtes HTTP**
  que le code frontend. L'aller-retour QR (`qrcode` → `jsqr`) vérifié
  séparément en Node avec un vrai token de billet : décodage exact.
  Données de test nettoyées après coup, vérifié par comptage (0 ligne
  restante).

**Décisions techniques :**
- **Le navigateur appelle FastAPI directement** (pas de proxy Next.js) :
  plus simple, cohérent avec le choix JWT de M5 (un en-tête
  `Authorization`, pas de cookie à faire transiter).
- Simulation de paiement exposée dans l'UI (`/commande/...`) quand
  `payment_url` est `null` (signe que le provider actif est `simulator`,
  pas CinetPay) — clairement étiqueté « démo portfolio », cohérent avec
  l'absence d'organisateurs réels/identifiants CinetPay à ce stade.
- Dashboard organisateur protégé **côté client seulement** (vérification du
  JWT dans `localStorage`, redirection sinon) — pas de middleware Next.js
  ni de rendu serveur conditionnel : suffisant ici, la vraie protection
  reste côté API (`GET /organizers/me/dashboard` exige un JWT valide et ne
  retourne que les événements de l'organisateur authentifié).

**Point ouvert signalé :** la capture caméra (`getUserMedia`) et la boucle
de détection QR sur les frames vidéo n'ont pas pu être testées avec une
vraie caméra dans cet environnement (CLI, pas de navigateur graphique) —
seule la logique d'encodage/décodage QR elle-même a été vérifiée par un
aller-retour réel. À tester manuellement dans un vrai navigateur avant
toute démonstration en conditions réelles.

**Prochain jalon (Mn) :** vérification complète `docker compose up
--build`, assignation de sièges numérotés (point ouvert depuis M3),
finalisation des README, proposition d'intégration au portfolio (diff
soumis avant tout commit dans `c:\Portfolio`).
