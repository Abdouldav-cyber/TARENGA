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


class Club(models.Model):
    CLUB_TYPES = (
        ('rotary', 'Rotary'),
        ('rotaract', 'Rotaract'),
        ('interact', 'Interact'),
    )
    name = models.CharField(max_length=150)
    club_type = models.CharField(max_length=20, choices=CLUB_TYPES, default='rotary')
    creation_date = models.DateField(null=True, blank=True)
    meeting_days = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    sponsor_club = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'club_type': 'rotary'})
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Club"
        verbose_name_plural = "Clubs"

    def __str__(self):
        return f"{self.name} ({self.get_club_type_display()}) - {self.country}"


class Mandat(models.Model):
    start_year = models.IntegerField(help_text="Année de début (ex: 2026)")
    end_year = models.IntegerField(help_text="Année de fin (ex: 2027)")
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Mandat"
        verbose_name_plural = "Mandats"

    def __str__(self):
        return f"{self.start_year}-{self.end_year}"


class ClubTax(models.Model):
    STATUS_CHOICES = (
        ('paye', 'Payé'),
        ('partiel', 'Partiel'),
        ('non_paye', 'Non Payé'),
        ('en_retard', 'En retard'),
    )
    club = models.ForeignKey(Club, on_delete=models.CASCADE, related_name='taxes')
    mandat = models.ForeignKey(Mandat, on_delete=models.CASCADE, related_name='taxes')
    amount_expected = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='non_paye')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Taxe Club"
        verbose_name_plural = "Taxes Clubs"
        unique_together = ('club', 'mandat')

    def __str__(self):
        return f"Taxe {self.club.name} - Mandat {self.mandat}"


class Participant(AbstractUser):
    # UUID as primary key for better security and QR code generation
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Custom fields for Rotary/Rotaract
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    whatsapp = models.CharField(max_length=20, unique=True, blank=True, null=True)
    
    # OTP Verification
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    
    district = models.CharField(max_length=50, blank=True, null=True, help_text="Ex: 9101")
    pays = models.CharField(max_length=100, blank=True, null=True)
    club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
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
    
    # Phase 5: Event Packs et Procuration
    pack = models.ForeignKey('EventPack', on_delete=models.SET_NULL, null=True, blank=True, related_name='participants')
    is_procuration = models.BooleanField(default=False)
    procuration_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='inscrits_par_procuration')

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
    PAYMENT_PLAN_CHOICES = (
        ('comptant', 'Comptant'),
        ('tontine', 'Par Tontine (Échelonné)'),
    )
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, null=True, blank=True)
    payment_plan = models.CharField(max_length=20, choices=PAYMENT_PLAN_CHOICES, default='comptant')
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

# --- MODULE DONS ---
class Donation(models.Model):
    BENEFICIARY_CHOICES = (
        ('soi', 'Pour soi-même'),
        ('club', 'Pour son club'),
        ('personne', 'Pour une autre personne'),
        ('organisation', 'Pour une organisation'),
    )
    STATUS_CHOICES = (
        ('paye', 'Payé'),
        ('en_attente', 'En attente'),
        ('echoue', 'Échoué'),
    )
    donateur_user = models.ForeignKey(Participant, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations')
    is_anonymous = models.BooleanField(default=False)
    
    beneficiary_type = models.CharField(max_length=20, choices=BENEFICIARY_CHOICES, default='soi')
    beneficiary_club = models.ForeignKey(Club, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations_received')
    beneficiary_name = models.CharField(max_length=150, blank=True, null=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    message = models.TextField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente')
    payment_method = models.CharField(max_length=20, choices=Payment.METHOD_CHOICES, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Don"
        verbose_name_plural = "Dons"

    def __str__(self):
        return f"Don de {self.amount} FCFA"

# --- MODULE BRAND CENTER ---
class Post(models.Model):
    author = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='posts')
    text = models.TextField()
    video_url = models.URLField(blank=True, null=True)
    likes_count = models.IntegerField(default=0)
    comments_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Post by {self.author.username} at {self.created_at}"

class PostImage(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='post_images/')
    sort_order = models.IntegerField(default=0)

class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Participant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    author = models.ForeignKey(Participant, on_delete=models.CASCADE)
    text = models.TextField()
    likes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)

class CommentLike(models.Model):
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(Participant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('comment', 'user')

# --- MODULE ÉVÉNEMENTS AVANCÉS ---
class EventPack(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='packs')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price_fcfa = models.DecimalField(max_digits=10, decimal_places=2)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.event.name}"

class EventActivity(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='activities')
    name = models.CharField(max_length=100)
    price_fcfa = models.DecimalField(max_digits=10, decimal_places=2)
    price_usd = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_daily = models.BooleanField(default=False, help_text="True si récurrent par jour")

    def __str__(self):
        return f"{self.name} - {self.event.name}"

# ==========================================
# NOUVEAUX MODÈLES (MVP FIN) - DYNAMIC CONTENT, PROGRAM & NOTIFICATIONS
# ==========================================

class HomepageContent(models.Model):
    rrd_word = models.TextField("Mot du RRD", blank=True)
    rrd_photo = models.ImageField("Photo du RRD", upload_to='homepage/', blank=True, null=True)
    governor_word = models.TextField("Mot du Gouverneur", blank=True)
    governor_photo = models.ImageField("Photo du Gouverneur", upload_to='homepage/', blank=True, null=True)
    banner_image = models.ImageField("Bannière Pays", upload_to='homepage/', blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Contenu Page d'Accueil"
        verbose_name_plural = "Contenu Page d'Accueil"

    def __str__(self):
        return "Configuration de la Page d'Accueil"

class EventDay(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='days')
    date = models.DateField()
    title = models.CharField("Titre de la journée", max_length=200)

    class Meta:
        ordering = ['date']
        verbose_name = "Jour du Programme"
        verbose_name_plural = "Jours du Programme"

    def __str__(self):
        return f"{self.date} - {self.title}"

class EventSession(models.Model):
    day = models.ForeignKey(EventDay, on_delete=models.CASCADE, related_name='sessions')
    start_time = models.TimeField("Heure de début")
    end_time = models.TimeField("Heure de fin")
    title = models.CharField("Titre de la session", max_length=200)
    description = models.TextField("Description", blank=True)
    location = models.CharField("Lieu", max_length=200, blank=True)
    speakers = models.CharField("Intervenants", max_length=200, blank=True)

    class Meta:
        ordering = ['start_time']
        verbose_name = "Session du Programme"
        verbose_name_plural = "Sessions du Programme"

    def __str__(self):
        return f"{self.start_time} - {self.title}"

class Notification(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    type_notif = models.CharField(max_length=50, choices=[('info', 'Information'), ('payment', 'Paiement'), ('alert', 'Alerte')], default='info')

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"Notif {self.id} - {self.participant.email}"
