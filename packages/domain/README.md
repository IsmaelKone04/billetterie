# domain

Schémas partagés et machine à états achat/billet (état commande :
CREEE → PAIEMENT_EN_ATTENTE → PAYEE → BILLETS_EMIS, branches ECHOUEE /
REMBOURSEE / ANNULEE). Source de vérité consommée par `admin-django` et
`api-fastapi`.

**État : M3 — machine à états de la commande.** `domain/order_state_machine.py`
définit `OrderStatus`, les transitions autorisées (`ORDER_TRANSITIONS`) et
`verifier_transition()` (lève `TransitionOrderInvalide` sinon). Pattern porté
de monbail (`escrow-state-machine.ts`), en Python puisque les deux
consommateurs (`admin-django`, `api-fastapi`) sont eux-mêmes en Python — pas
besoin de dupliquer le graphe de transitions dans chaque service.

## Installer dans un venv

```bash
pip install -e ../../packages/domain
```

(déjà référencé dans les `requirements.txt` d'`admin-django` et
`api-fastapi` via `-e ../../packages/domain`.)
