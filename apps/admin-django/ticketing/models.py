import uuid

from django.conf import settings
from django.db import models

from domain.order_state_machine import ORDER_STATUS_LABELS, OrderStatus


class Organizer(models.Model):
    """Compte organisateur — un utilisateur peut créer/gérer des événements
    (marketplace multi-organisateurs). Inscription en libre-service côté
    api-fastapi (email + mot de passe propres à Organizer, JWT signé —
    voir app/services/auth.py) : ce n'est PAS un compte staff Django, donc
    `user` reste optionnel (lien manuel possible si un organisateur a aussi
    besoin d'un accès à l'admin Django)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organizer_profile",
        verbose_name="utilisateur",
        null=True,
        blank=True,
    )
    display_name = models.CharField("nom affiché", max_length=150)
    email = models.EmailField("e-mail", unique=True)
    password_hash = models.CharField(
        "mot de passe (haché)", max_length=128, editable=False
    )
    phone = models.CharField("téléphone", max_length=30, blank=True)
    mobile_money_account = models.CharField(
        "compte Mobile Money (reversement)", max_length=50, blank=True
    )
    created_at = models.DateTimeField("créé le", auto_now_add=True)

    class Meta:
        verbose_name = "organisateur"
        verbose_name_plural = "organisateurs"

    def __str__(self):
        return self.display_name


class Venue(models.Model):
    """Lieu physique d'un événement."""

    name = models.CharField("nom", max_length=150)
    city = models.CharField("ville", max_length=100)
    address = models.CharField("adresse", max_length=255, blank=True)

    class Meta:
        verbose_name = "lieu"
        verbose_name_plural = "lieux"

    def __str__(self):
        return f"{self.name} ({self.city})"


class Section(models.Model):
    """Une zone du plan de salle d'un lieu : soit à places numérotées, soit
    une zone générique à capacité limitée (debout / places libres)."""

    venue = models.ForeignKey(
        Venue, on_delete=models.CASCADE, related_name="sections", verbose_name="lieu"
    )
    name = models.CharField("nom", max_length=100)
    has_numbered_seats = models.BooleanField(
        "places numérotées", default=False
    )
    capacity = models.PositiveIntegerField(
        "capacité",
        help_text="Utilisée pour les zones sans places numérotées ; "
        "ignorée si des sièges (Seat) sont définis pour cette section.",
    )

    class Meta:
        verbose_name = "section"
        verbose_name_plural = "sections"
        unique_together = ("venue", "name")

    def __str__(self):
        return f"{self.venue.name} — {self.name}"


class Seat(models.Model):
    """Un siège numéroté, uniquement pour les sections à places numérotées."""

    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, related_name="seats", verbose_name="section"
    )
    row = models.CharField("rangée", max_length=10)
    number = models.CharField("numéro", max_length=10)

    class Meta:
        verbose_name = "siège"
        verbose_name_plural = "sièges"
        unique_together = ("section", "row", "number")
        ordering = ["row", "number"]

    def __str__(self):
        return f"{self.section} {self.row}{self.number}"


class Event(models.Model):
    class Statut(models.TextChoices):
        BROUILLON = "brouillon", "Brouillon"
        PUBLIE = "publie", "Publié"
        TERMINE = "termine", "Terminé"
        ANNULE = "annule", "Annulé"

    organizer = models.ForeignKey(
        Organizer,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="organisateur",
    )
    venue = models.ForeignKey(
        Venue,
        on_delete=models.PROTECT,
        related_name="events",
        verbose_name="lieu",
    )
    title = models.CharField("titre", max_length=200)
    description = models.TextField("description", blank=True)
    starts_at = models.DateTimeField("date et heure de début")
    status = models.CharField(
        "statut", max_length=20, choices=Statut.choices, default=Statut.BROUILLON
    )
    created_at = models.DateTimeField("créé le", auto_now_add=True)
    updated_at = models.DateTimeField("mis à jour le", auto_now=True)

    class Meta:
        verbose_name = "événement"
        verbose_name_plural = "événements"
        ordering = ["starts_at"]

    def __str__(self):
        return self.title


class TicketType(models.Model):
    """Un tarif vendable pour un événement — remplace le dict TARIFS codé en
    dur de l'ancienne maquette. Peut être rattaché à une section du plan de
    salle (places numérotées) ou rester générique (quota simple)."""

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="ticket_types", verbose_name="événement"
    )
    section = models.ForeignKey(
        Section,
        on_delete=models.PROTECT,
        related_name="ticket_types",
        verbose_name="section",
        null=True,
        blank=True,
        help_text="Optionnel : laisser vide pour un tarif non lié à une zone précise.",
    )
    name = models.CharField("nom", max_length=100)
    price = models.DecimalField("prix (FCFA)", max_digits=10, decimal_places=2)
    quota = models.PositiveIntegerField("quota disponible")
    sales_start = models.DateTimeField("ouverture des ventes", null=True, blank=True)
    sales_end = models.DateTimeField("fin des ventes", null=True, blank=True)

    class Meta:
        verbose_name = "tarif"
        verbose_name_plural = "tarifs"
        ordering = ["event", "price"]

    def __str__(self):
        return f"{self.event.title} — {self.name} ({self.price} FCFA)"


class Order(models.Model):
    """Commande d'un acheteur pour un événement — achat public sans compte
    utilisateur (email/téléphone suffisent). Statut piloté par la machine à
    états partagée `domain.order_state_machine` (transitions vérifiées côté
    api-fastapi avant toute écriture)."""

    STATUS_CHOICES = [(status.value, ORDER_STATUS_LABELS[status]) for status in OrderStatus]

    event = models.ForeignKey(
        Event, on_delete=models.PROTECT, related_name="orders", verbose_name="événement"
    )
    buyer_email = models.EmailField("e-mail acheteur")
    buyer_phone = models.CharField("téléphone acheteur", max_length=30)
    status = models.CharField(
        "statut", max_length=30, choices=STATUS_CHOICES, default=OrderStatus.CREEE.value
    )
    amount_total = models.DecimalField("montant total (FCFA)", max_digits=10, decimal_places=2)
    payment_provider = models.CharField(
        "provider de paiement", max_length=20, blank=True, help_text="'simulator' ou 'cinetpay'"
    )
    transaction_id = models.CharField(
        "identifiant de transaction",
        max_length=64,
        unique=True,
        help_text="Généré à la création de la commande, transmis au provider de paiement.",
    )
    created_at = models.DateTimeField("créée le", auto_now_add=True)
    updated_at = models.DateTimeField("mise à jour le", auto_now=True)

    class Meta:
        verbose_name = "commande"
        verbose_name_plural = "commandes"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Commande {self.transaction_id} ({self.get_status_display()})"


class Ticket(models.Model):
    """Un billet vendu — un par place. `qr_secret` est le token encodé dans
    le QR (jamais l'ID brut, pour empêcher la fabrication de faux billets)."""

    class Statut(models.TextChoices):
        VALIDE = "valide", "Valide"
        SCANNE = "scanne", "Scanné"
        ANNULE = "annule", "Annulé"

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="tickets", verbose_name="commande"
    )
    ticket_type = models.ForeignKey(
        TicketType, on_delete=models.PROTECT, related_name="tickets", verbose_name="tarif"
    )
    seat = models.ForeignKey(
        Seat,
        on_delete=models.PROTECT,
        related_name="tickets",
        verbose_name="siège",
        null=True,
        blank=True,
    )
    qr_secret = models.CharField(
        "secret QR", max_length=64, unique=True, default=uuid.uuid4, editable=False
    )
    status = models.CharField(
        "statut", max_length=20, choices=Statut.choices, default=Statut.VALIDE
    )
    scanned_at = models.DateTimeField("scanné le", null=True, blank=True)
    scanned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="tickets_scanned",
        verbose_name="scanné par",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "billet"
        verbose_name_plural = "billets"

    def __str__(self):
        return f"Billet {self.pk} — {self.ticket_type} ({self.get_status_display()})"


class PaymentEvent(models.Model):
    """Journal d'audit de chaque webhook de paiement reçu (CinetPay ou
    simulateur) — signature vérifiée ou non, appliqué ou non. Déduplication
    par `provider_event_id` (pattern repris de monbail)."""

    order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        related_name="payment_events",
        verbose_name="commande",
        null=True,
        blank=True,
    )
    provider = models.CharField("provider", max_length=20)
    provider_event_id = models.CharField(
        "identifiant d'événement (provider)", max_length=100, unique=True
    )
    event_type = models.CharField("type d'événement", max_length=50, blank=True)
    signature_valid = models.BooleanField("signature valide")
    raw_payload = models.JSONField("payload brut")
    outcome = models.CharField(
        "résultat",
        max_length=20,
        help_text="'applique', 'ignore', 'rejete' ou 'signature_invalide'.",
    )
    received_at = models.DateTimeField("reçu le", auto_now_add=True)
    processed_at = models.DateTimeField("traité le", null=True, blank=True)

    class Meta:
        verbose_name = "événement de paiement"
        verbose_name_plural = "événements de paiement"
        ordering = ["-received_at"]

    def __str__(self):
        return f"{self.provider}:{self.provider_event_id} ({self.outcome})"
