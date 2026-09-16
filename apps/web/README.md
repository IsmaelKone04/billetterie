# web

Frontend Next.js (App Router, TypeScript, Tailwind CSS) : vitrine, achat,
« mes billets », scan de billets, inscription/connexion organisateur,
dashboard analytics. Ne parle qu'aux API REST (`api-fastapi` pour tout ;
`admin-django` n'est pas appelé directement par ce frontend).

**État : Mn — frontend complet, vérifié via Docker Compose.**

- `/` — catalogue des événements publiés.
- `/evenements/[id]` — détail d'un événement, tarifs, formulaire d'achat.
- `/commande/[transactionId]` — statut de la commande ; si le provider de
  paiement est `simulator` (pas d'identifiants CinetPay réels), propose de
  simuler l'issue du paiement (démo portfolio) ; affiche les billets (QR)
  une fois `billets_emis`.
- `/mes-billets` — retrouver ses billets avec le numéro de commande + e-mail.
- `/scan` — scan de billets par le personnel (caméra via `getUserMedia` +
  décodage QR côté client avec `jsqr`, ou saisie manuelle du token en
  secours), protégé par la clé `X-Scan-Key`.
- `/organisateurs/inscription`, `/organisateurs/connexion` — auth
  organisateur par JWT (stocké en `localStorage`, envoyé en
  `Authorization: Bearer`).
- `/organisateurs/tableau-de-bord` — analytics par événement (billets
  vendus, remplissage, revenu), protégé côté client par la présence d'un
  token valide (redirection vers la connexion sinon).

## Lancer en local

```bash
cd apps/web
npm install
npm run dev
```

Nécessite `api-fastapi` démarré (voir son README) et accessible à l'URL
définie par `NEXT_PUBLIC_API_URL` dans `apps/web/.env.local` (voir
`.env.example` à la racine du repo — par défaut `http://localhost:8000`).
`api-fastapi` doit aussi autoriser cette origine en CORS
(`CORS_ALLOWED_ORIGINS`, `http://localhost:3000` par défaut).

Ou via Docker (voir `docker/web.Dockerfile` et le service `web` de
`docker-compose.yml` à la racine) : `docker compose up --build web`. Deux
variables d'URL distinctes y sont utilisées — voir `src/lib/api.ts` et
`.env.example` (`NEXT_PUBLIC_API_URL` pour le navigateur,
`API_INTERNAL_URL` pour les composants serveur qui tournent dans le
conteneur `web` lui-même).

## Vérification

Build (`npm run build`) et lint (`npm run lint`) systématiquement propres.
Flux achat → paiement simulé → « mes billets » → scan vérifié de bout en
bout à travers la stack Docker complète (`docker compose up --build`),
en appelant les ports publiés sur l'hôte avec les mêmes requêtes que le
code frontend (mêmes types TypeScript que les schémas FastAPI), et en
chargeant les pages server-rendues via `curl`. L'encodage/décodage QR
(`qrcode` + `jsqr`) vérifié par un aller-retour complet en Node avec un
vrai token de billet.

**Non testé ici, nécessite un vrai navigateur avec caméra :** la capture
vidéo `getUserMedia` et la boucle de détection QR sur les frames — signalé
plutôt qu'ignoré, voir `docs/RAPPORT.md`.
