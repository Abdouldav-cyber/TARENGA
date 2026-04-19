from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile

class Event(models.Model):
    EVENT_TYPES = (
        ('rotary', 'Rotary (ACD)'),
        ('rotaract', 'Rotaract (ACD)'),
        ('both', 'Les Deux'),
    )
    name = models.CharField(max_length=100)
    event_type = models.CharField(max_length=15, choices=EVENT_TYPES, default='rotary')
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"

    def __str__(self):
        return f"{self.name} ({self.get_event_type_display()})"


class Participant(AbstractUser):
    # UUID as primary key for better security and QR code generation
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Custom fields for Rotary/Rotaract
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    district = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: 9101")
    pays = models.CharField(max_length=100, blank=True, null=True)
    club = models.CharField(max_length=150, blank=True, null=True)
    poste = models.CharField(max_length=100, blank=True, null=True)
    
    PARTICIPANT_TYPES = (
        ('participant', 'Participant'),
        ('organisateur', 'Organisateur'),
        ('invite', 'Invité'),
        ('sponsor', 'Sponsor'),
    )
    type_participant = models.CharField(max_length=20, choices=PARTICIPANT_TYPES, default='participant')
    
    photo = models.ImageField(upload_to='photos_participants/', blank=True, null=True)
    event_choice = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = "Participant"
        verbose_name_plural = "Participants"

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.club}"


class Payment(models.Model):
    STATUS_CHOICES = (
        ('paye', 'Payé'),
        ('partiel', 'Partiel'),
        ('non_paye', 'Non Payé'),
    )
    METHOD_CHOICES = (
        ('wave', 'Wave'),
        ('orange_money', 'Orange Money'),
        ('cb', 'Carte Bancaire'),
    )
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='payments')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    amount_total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='non_paye')
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    date_payment = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"

    def __str__(self):
        return f"Paiement de {self.participant} - {self.amount_paid} ({self.get_status_display()})"


class Logistics(models.Model):
    participant = models.OneToOneField(Participant, on_delete=models.CASCADE, related_name='logistics')
    arrival_datetime = models.DateTimeField(null=True, blank=True)
    transport_mode = models.CharField(max_length=100, blank=True, null=True)
    hotel_name = models.CharField(max_length=150, blank=True, null=True)
    room_number = models.CharField(max_length=20, blank=True, null=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    class Meta:
        verbose_name = "Logistique"
        verbose_name_plural = "Logistique (Hôtels & Billets)"

    def generate_qr_code(self):
        """Méthode magique pour générer le QR code Crypté"""
        if not self.qr_code:
            # Données secrètes cryptées contenant l'ID et l'Événement
            qr_data = f"TÉRANGA_2027|ID:{self.participant.id}|{self.participant.get_full_name()}|STATUT:Valide"
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            
            filename = f"qr_{self.participant.id}.png"
            self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)
            self.save()

    def __str__(self):
        return f"Logistique: {self.participant}"
