# domain

Schémas partagés et machine à états achat/billet (état commande :
CREEE → PAIEMENT_EN_ATTENTE → PAYEE → BILLETS_EMIS, branches ECHOUEE /
REMBOURSEE / ANNULEE). Source de vérité consommée par `admin-django` et
`api-fastapi`.

**État : vide, à implémenter au jalon M1.**
