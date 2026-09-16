# syntax=docker/dockerfile:1
# Image web (frontend Next.js, sortie standalone) — multi-étapes.
# Contexte de build attendu : racine du monorepo.

FROM node:22-alpine AS base
WORKDIR /repo/apps/web

FROM base AS deps
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci

FROM deps AS build
# Inlinée dans le bundle client au build (NEXT_PUBLIC_*) : doit pointer vers
# l'URL de api-fastapi telle que joignable depuis le NAVIGATEUR (le port
# publié sur l'hôte par docker-compose), pas le nom de service interne.
ARG NEXT_PUBLIC_API_URL=http://localhost:8010
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1
COPY apps/web ./
RUN npm run build

FROM node:22-alpine AS runtime
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
# Next standalone lit HOSTNAME/PORT ; sans ça il se lie au hostname du
# conteneur et le healthcheck sur localhost ne répond pas.
ENV HOSTNAME=0.0.0.0
ENV PORT=3000
WORKDIR /app
COPY --from=build --chown=node:node /repo/apps/web/.next/standalone ./
COPY --from=build --chown=node:node /repo/apps/web/.next/static ./.next/static
COPY --from=build --chown=node:node /repo/apps/web/public ./public
USER node
EXPOSE 3000
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=6 \
  CMD node -e "require('http').get('http://localhost:3000/',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"
CMD ["node", "server.js"]
