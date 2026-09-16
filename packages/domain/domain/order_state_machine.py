"""Machine à états de la commande (Order) — source de vérité unique des
transitions autorisées, consommée par `admin-django` (choix du champ status)
et `api-fastapi` (logique d'achat/paiement). Pattern repris de monbail
(packages/domain/src/escrow-state-machine.ts), porté en Python."""

from enum import Enum


class OrderStatus(str, Enum):
    CREEE = "creee"
    PAIEMENT_EN_ATTENTE = "paiement_en_attente"
    PAYEE = "payee"
    BILLETS_EMIS = "billets_emis"
    ECHOUEE = "echouee"
    REMBOURSEE = "remboursee"
    ANNULEE = "annulee"


ORDER_STATUS_LABELS: dict[OrderStatus, str] = {
    OrderStatus.CREEE: "Créée",
    OrderStatus.PAIEMENT_EN_ATTENTE: "Paiement en attente",
    OrderStatus.PAYEE: "Payée",
    OrderStatus.BILLETS_EMIS: "Billets émis",
    OrderStatus.ECHOUEE: "Échouée",
    OrderStatus.REMBOURSEE: "Remboursée",
    OrderStatus.ANNULEE: "Annulée",
}

ORDER_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.CREEE: frozenset({OrderStatus.PAIEMENT_EN_ATTENTE, OrderStatus.ANNULEE}),
    OrderStatus.PAIEMENT_EN_ATTENTE: frozenset(
        {OrderStatus.PAYEE, OrderStatus.ECHOUEE, OrderStatus.ANNULEE}
    ),
    OrderStatus.PAYEE: frozenset({OrderStatus.BILLETS_EMIS, OrderStatus.REMBOURSEE}),
    OrderStatus.BILLETS_EMIS: frozenset({OrderStatus.REMBOURSEE}),
    OrderStatus.ECHOUEE: frozenset(),
    OrderStatus.REMBOURSEE: frozenset(),
    OrderStatus.ANNULEE: frozenset(),
}


class TransitionOrderInvalide(Exception):
    """Levée quand une transition d'état de commande n'est pas autorisée."""


def transition_autorisee(depuis: OrderStatus, vers: OrderStatus) -> bool:
    return vers in ORDER_TRANSITIONS[depuis]


def verifier_transition(depuis: OrderStatus, vers: OrderStatus) -> None:
    if not transition_autorisee(depuis, vers):
        raise TransitionOrderInvalide(f"transition refusée : {depuis.value} -> {vers.value}")
