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

## 2026-09-16 — Mn : Docker Compose de bout en bout, sièges numérotés, finalisation

**Docker Compose complet :**
- Trois `Dockerfile` créés (`docker/admin.Dockerfile`, `docker/api.Dockerfile`,
  `docker/web.Dockerfile`), contexte de build = racine du monorepo (comme
  `monbail`, pour installer `packages/domain`). Django/FastAPI : image
  `python:3.13-slim`, install en `cd apps/<app> && pip install -r
  requirements.txt` — **piège découvert** : `-e ../../packages/domain` dans
  `requirements.txt` est résolu par pip relativement au **répertoire courant
  au moment de l'install**, pas au fichier requirements.txt lui-même (malgré
  ce qu'indique la doc pip ≥ 21.3 pour les chemins simples) ; un premier essai
  lançant `pip install -r apps/.../requirements.txt` depuis `/repo` a échoué
  (« not a valid editable requirement »), corrigé en `cd`-ant dans le dossier
  de l'app avant l'install. Web : multi-étapes Node 22 alpine, sortie
  `standalone` (ajout de `output: "standalone"` à `next.config.ts`, absent
  jusqu'ici).
- `docker-compose.yml` : les trois services (`admin-django`, `api-fastapi`,
  `web`), jusque-là commentés, activés avec healthchecks, `cap_drop: [ALL]`,
  `no-new-privileges`. Ports hôte : `admin-django` sur 8000, `api-fastapi`
  décalé sur **8010** (8000 déjà pris par Django), `web` sur 3000 — même
  logique de décalage que Postgres/Redis en haut du fichier.
- Ajout de `GET /health/` côté Django (`config/urls.py`) — absent jusqu'ici,
  nécessaire pour le healthcheck Docker (FastAPI avait déjà `/health`).

**Bug réel trouvé et corrigé — URL API selon le contexte d'exécution :**
Next.js exécute le code des composants serveur (catalogue, détail
événement) **dans le conteneur `web` lui-même**, pas dans le navigateur.
`NEXT_PUBLIC_API_URL` est inlinée au build pour le navigateur
(`http://localhost:8010`, le port publié sur l'hôte) — mais ce conteneur ne
peut pas joindre `api-fastapi` via `localhost:8010` (c'est son propre
`localhost`, pas celui de l'hôte). Constaté concrètement : `/` chargeait
sans erreur mais sans événements (fetch serveur échoué, avalé par le
try/catch de la page), et `/evenements/[id]` renvoyait une 500 (erreur
serveur non catchée, relancée volontairement pour tout sauf 404). Corrigé en
ajoutant une seconde variable, `API_INTERNAL_URL` (`http://api-fastapi:8000`,
nom du service Docker), lue **uniquement côté serveur** (`typeof window ===
"undefined"` dans `lib/api.ts`) — jamais inlinée, donc pas besoin de
rebuild pour en changer la valeur en prod. Sans Docker (dev local),
`API_INTERNAL_URL` est absente et tout retombe sur `NEXT_PUBLIC_API_URL`,
puisque serveur et navigateur tournent alors sur le même hôte.

**Vérification de bout en bout réelle, à travers les conteneurs (pas
`pytest`, pas `next dev`) :** `docker compose up --build` (les 5 services
sains), puis données de test insérées en SQL brut dans le conteneur
`postgres`, et flux rejoué en HTTP réel contre les ports publiés
(`localhost:8000/8010/3000`) : catalogue → détail événement → commande →
paiement simulé → billets émis → scan (accepté puis refusé en double) →
inscription/connexion organisateur (JWT) → dashboard analytics ; pages
Next.js `/`, `/evenements/[id]`, `/mes-billets`, `/scan`,
`/organisateurs/*` toutes vérifiées en 200 avec le contenu réel affiché
côté serveur. Admin Django accessible sur `/admin/login/`. Données de test
nettoyées et vérifiées à 0 ligne après coup.

**Sièges numérotés (point ouvert depuis M3) :** implémenté côté
`api-fastapi`. `Section`/`Seat` ajoutés aux modèles SQLAlchemy (existaient
déjà côté Django/admin, jamais lus côté API). Dans `services/orders.py`, à
la création d'une commande, pour chaque tarif lié à une section à places
numérotées (`has_numbered_seats=True`) : calcul des sièges déjà retenus par
des commandes non terminales du **même événement** sur cette section
(même portée que le quota — `RESERVING_STATUSES`), attribution des
premiers sièges libres (triés rangée/numéro), et **409 explicite**
(`SeatsUnavailable`) si plus assez de sièges libres — avant même la
création de la commande, donc aucune ligne orpheline. Le `seat_label`
(ex. « A12 ») est renvoyé dans `GET /orders/{transaction_id}/tickets` et
affiché sur le billet côté frontend (`TicketList.tsx`). Portée volontairement
limitée au cas normal (une section ↔ un tarif) ; le cas d'école « deux
tarifs différents pointant vers la même section » n'a pas de verrouillage
dédié au-delà du verrou Redis déjà posé par tarif — non traité, jugé hors
scope pour un MVP.
- Tests : 2 nouveaux (`test_numbered_seats_assigned_and_never_reused` :
  attribution, non-réutilisation, refus explicite si plus de sièges libres ;
  `test_seated_ticket_appears_with_seat_label`). Suite complète :
  21 → **23 tests, tous verts**.
- **Bug de pollution de données trouvé pendant ces tests** (même discipline
  qu'à M3) : le nouveau fixture `numbered_seats` supprimait d'abord le
  `TicketType` puis les `Ticket` qui le référencent encore
  (`on_delete=PROTECT` côté Django) → `IntegrityError`, qui interrompait la
  chaîne de nettoyage des fixtures dépendantes (`catalogue` ne s'exécutait
  plus derrière) et laissait des lignes orphelines (organisateur, lieu,
  événement, commandes, billets) dans la base partagée. Corrigé en
  inversant l'ordre (billets d'abord, tarif ensuite). Lignes orphelines
  identifiées et supprimées manuellement, comptage revérifié à 0 partout.

**Fait aussi :** README racine et des trois apps mis à jour (bannière
d'état, sièges numérotés retiré des points ouverts).

**Points ouverts, non traités ici (déjà connus, toujours valables) :**
- Pas de timeout/libération automatique des commandes bloquées en
  `paiement_en_attente` (M3).
- `CinetPayProvider` jamais testé contre la vraie API CinetPay (M3).
- Scan protégé par une clé partagée, pas par compte staff individuel ;
  `Ticket.scanned_by` reste `NULL` (M4).
- Pas de limitation de débit sur `POST /organizers/login` (M5).
- Capture caméra (`getUserMedia`) et boucle de détection QR toujours pas
  testées avec un vrai navigateur/une vraie caméra (M6) — à faire avant
  toute démo réelle.

**Prochaine étape :** proposition d'intégration au portfolio
(`c:\Portfolio`) — diff soumis avant tout commit, comme convenu.

## 2026-09-16 — Post-Mn : test utilisateur réel, bug de build Docker trouvé, billet PDF, refonte visuelle

Ismaël a testé la plateforme lui-même après Mn (compte superuser créé :
`admin` / mot de passe communiqué séparément) et remonté deux problèmes :
le bouton « simuler le paiement » introuvable, et une interface jugée trop
plate. Il a aussi demandé si le paiement générait un billet PDF — non,
jusqu'ici.

**Bug réel trouvé et corrigé — mauvais port API dans le bundle navigateur :**
Le bouton existait bel et bien dans le DOM (confirmé via Chrome headless
avec exécution JS réelle), mais la page affichait « Impossible de contacter
l'API. ». Diagnostic par les logs console de Chrome (`--enable-logging`) :
`Access to fetch at 'http://localhost:8000/orders/.../tickets...' ... has
been blocked by CORS policy`. Le navigateur appelait le port **8000**
(admin-django) au lieu de **8010** (api-fastapi, port décalé pour cohabiter
avec Django dans Docker Compose). Cause : `docker-compose.yml` construisait
l'image `web` avec `NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL:-http://localhost:8010}`
— mais `NEXT_PUBLIC_API_URL` est **aussi** défini dans `.env` (`=http://
localhost:8000`, pour `npm run dev` hors Docker, où api-fastapi tourne
seul sur son port par défaut). docker-compose substitue silencieusement la
valeur de `.env` dès qu'une variable du même nom y existe, écrasant le
`:-http://localhost:8010` de secours qui ne servait donc jamais. Corrigé
en renommant la variable utilisée par le build Docker en
`WEB_DOCKER_NEXT_PUBLIC_API_URL` (distincte, documentée dans `.env.example`),
pour qu'elle ne puisse plus jamais être masquée par la variable du même nom
utilisée pour le dev local hors Docker — deux contextes, deux valeurs,
donc deux noms. Reconstruit et revérifié via Chrome headless avec capture
des logs console (plus d'erreur CORS, bouton et confirmation de paiement
bien affichés).

**Leçon** : `curl` ne suffit pas à vérifier une page React côté client —
il ne voit que le HTML statique avant hydratation. Le premier essai de
vérification via Chrome headless (`--dump-dom`) avec `--virtual-time-budget`
a d'abord semblé donner un résultat instable (échec puis succès selon le
budget alloué), ce qui a failli faire passer ce vrai bug pour un artefact
de l'outil de test. Vérifié en répétant avec plusieurs budgets (4 s à 25 s) :
l'échec était **systématique**, donc réel — et la cause exacte trouvée en
activant les logs console de Chrome (`--enable-logging=stderr --v=1`), qui
donnent le message d'erreur CORS exact du navigateur, bien plus parlant que
deviner à partir du seul DOM final.

**Billet PDF (demandé) :** `jspdf` ajouté ; `lib/ticketPdf.ts` génère côté
client (comme le QR, jamais côté serveur) un PDF au format « billet »
paysage avec QR, titre/date/lieu de l'événement, tarif, siège si numéroté,
numéro de commande. Bouton « Télécharger (PDF) » sur chaque billet
(`TicketList.tsx`). A nécessité d'exposer `event_starts_at` et `venue` dans
`GET /orders/{transaction_id}/tickets` côté API (absents jusqu'ici, la
route ne renvoyait que `event_title`).

**Refonte visuelle de toute l'application** (`lucide-react` ajouté pour les
icônes) : dégradé indigo/violet en en-tête et boutons principaux, page
catalogue avec bandeau d'accroche et cartes d'événements illustrées, page
événement en deux colonnes (infos + formulaire d'achat en volet collant),
quantités de billets par steppers +/-, page de commande avec états
visuellement distincts (icônes succès/attente/échec, panneau de simulation
clairement démarqué de l'erreur), billets présentés en carte façon vrai
ticket (souche pointillée + QR), scan avec cadre caméra et états
succès/échec plus lisibles, tableau de bord organisateur avec cartes
statistiques et barres de remplissage. Testé après coup : `npm run build`
et `npm run lint` propres, suite `pytest` (23 tests) toujours verte,
parcours complet rejoué à travers les conteneurs Docker reconstruits.

**Fait aussi :** compte superuser Django `admin` créé/réinitialisé pour
qu'Ismaël puisse explorer le back-office ; un événement de démonstration
(« Nuit du Coupé-Décalé », tarif debout + section VIP à sièges numérotés)
seedé en base pour qu'il ait un vrai parcours à tester sans devoir créer
ses propres données au préalable.

## 2026-09-16 — Refonte visuelle de l'admin Django (style shadcn)

Demande explicite d'Ismaël après le test utilisateur : « restructure cette
page http://localhost:8000/admin/, je veux un beau rendu style shadcn ».
shadcn/ui est une bibliothèque de composants React — pas transposable
telle quelle sur du HTML/CSS généré par Django — donc reproduit son
langage visuel (palette neutre + accent indigo, cartes blanches
arrondies à bordure fine, ombres douces, typographie system-ui) plutôt que
les composants eux-mêmes.

**Réalisé :**
- `apps/admin-django/static/admin/css/custom_theme.css` : surcharge des
  variables CSS natives de l'admin Django 6.1 (`--primary`, `--body-bg`,
  `--button-bg`, etc., définies dans `base.css`/`dark_mode.css`), plus des
  règles ciblées pour les modules/cartes, la barre latérale, les tableaux
  de listes, les formulaires et la page de connexion (dégradé indigo/violet
  en en-tête, carte centrée). Couvre aussi le mode sombre natif de l'admin
  (`html[data-theme="dark"]`), pas seulement le mode clair.
- `apps/admin-django/templates/admin/base_site.html` : ajoute la feuille de
  style via `{% block extrastyle %}` — étend `admin/base.html` (pas
  `admin/base_site.html`, qui aurait pu créer une confusion sur quel
  fichier est réellement résolu par le chargeur de templates).
- `ticketing/admin.py` : `admin.site.site_header/site_title/index_title`
  fixés à « billetterie » (remplace « Django administration »).
- `TEMPLATES[0]["DIRS"]` ajouté dans `settings.py` pour que ce template
  personnalisé soit trouvé.

**Bug de spécificité CSS trouvé et corrigé :** le bouton « Rechercher » de
la barre d'outils des listes restait gris malgré la surcharge de
`--button-bg`. Cause : `admin/css/changelists.css` définit son propre
`#toolbar form input[type="submit"] { background: var(--body-bg); ... }`,
chargé **après** mon fichier (Django charge `changelists.css` dans le bloc
`extrastyle` de `change_list.html`, qui appelle `{{ block.super }}` — donc
mon lien `<link>` — avant d'ajouter le sien) ; à spécificité CSS égale,
la règle chargée en dernier gagne. Corrigé avec des `!important` ciblés sur
ce seul sélecteur — pragmatique, plutôt que restructurer l'ordre de
chargement des templates.

**Vérification visuelle réelle** (pas seulement `curl`, qui ne peut pas
juger du rendu) : Chrome headless piloté via le protocole CDP brut
(`--remote-debugging-port`, un script Node utilisant `fetch`/`WebSocket`
natifs pour ouvrir un onglet, injecter le cookie de session obtenu par une
connexion `curl` préalable, naviguer, puis `Page.captureScreenshot`) —
login, tableau de bord, liste d'événements et formulaire d'ajout
capturés et inspectés en image. `python manage.py check` sans erreur.

**Non couvert par cette passe (pas demandé, pas vérifié) :** pages
d'edit/detail plus complexes avec inlines (Order avec ses Ticket, par
exemple) — la palette générale s'applique partout via les variables CSS,
mais leur mise en page fine n'a pas été inspectée visuellement une à une.

## 2026-09-16 — Suite : « l'affichage est cassé » (retour utilisateur)

Ismaël a remonté un affichage cassé après la passe précédente, sans plus
de détail. Investigation complète avant de conclure quoi que ce soit.

**Démarche :** capture d'écran de chaque page principale à largeur normale
(login, dashboard, listes, formulaire d'ajout, fiche événement avec son
formset tabulaire Tarifs) — toutes correctes à 1600 px. Le formset
tabulaire de la fiche Événement (colonnes Section/Nom/Prix/Quota/dates/
Supprimer) semblait en revanche visuellement cassé (colonnes empilées
verticalement) une fois capturé à une largeur de fenêtre étroite (~700 px,
la largeur par défaut d'une fenêtre Chrome headless sans taille explicite).

**Vérifications pour isoler la cause réelle, avant de blâmer mon thème :**
- Rejoué la même capture avec `custom_theme.css` désactivé en direct dans
  la page (`link.disabled = true` via le protocole CDP) : le même rendu
  « cassé » apparaît à l'identique — donc **pas une régression introduite
  par ce thème**, un comportement déjà présent dans l'admin Django nu.
- Inspection des styles calculés et des rectangles réels de chaque
  cellule (`getBoundingClientRect`) : les cellules sont bien en
  `display: table-cell`, alignées à la même coordonnée Y, positionnées
  côte à côte (x croissant) — la table n'est **pas** structurellement
  cassée. Ce qui ressemblait à un empilement dans la capture d'écran était
  en réalité une table plus large que la fenêtre visible (7 colonnes),
  dont seules les 2-3 premières colonnes tiennent dans ~655 px de large ;
  le reste nécessite un défilement horizontal qui existe déjà nativement
  (`.wrapper { overflow-x: auto }`) mais dont les colonnes, sans largeur
  minimale, se tassaient au point de sembler illisibles/décousues au
  premier coup d'œil dans une capture partielle.

**Correctif appliqué malgré tout** (améliore un point rugueux réel, même
s'il préexistait) : largeur minimale de 900px imposée à la table du
formset tabulaire, pour que le défilement horizontal reste net (colonnes
lisibles) plutôt qu'un tassement qui donne l'impression d'un rendu cassé.

**Conclusion transmise à Ismaël :** rendu confirmé propre à largeur normale
sur toutes les pages testées ; le seul point trouvé (défilement horizontal
nécessaire sur les formsets à beaucoup de colonnes, en fenêtre étroite)
est désormais net plutôt que tassé, mais reste un défilement — pas un
tableau qui tient entièrement à l'écran sans action. Demande de précision
(capture d'écran ou taille de fenêtre) en attente pour confirmer si c'est
bien ce qu'il a vu, faute de quoi rien d'autre n'a pu être identifié comme
cassé après une vérification systématique.
