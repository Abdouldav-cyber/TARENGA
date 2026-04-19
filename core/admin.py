from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Participant, Event, Payment, Logistics

# Personnalisation de l'entête
admin.site.site_header = "Administration Teranga 2027"
admin.site.site_title = "Portail Admin Teranga"
admin.site.index_title = "Panneau de Gestion des Inscriptions"

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'event_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('event_type', 'is_active')
    search_fields = ('name',)

@admin.register(Participant)
class ParticipantAdmin(UserAdmin):
    # Fieldsets are necessary to display custom fields correctly over the AbstractUser ones
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Rotaract/Rotary', {'fields': ('whatsapp', 'district', 'pays', 'club', 'poste', 'type_participant', 'event_choice')}),
        ('Média', {'fields': ('photo',)}),
    )
    list_display = ('username', 'first_name', 'last_name', 'club', 'pays', 'type_participant')
    list_filter = ('type_participant', 'pays', 'district')
    search_fields = ('username', 'first_name', 'last_name', 'club', 'whatsapp')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('participant', 'amount_paid', 'amount_total', 'status', 'payment_method', 'date_payment')
    list_filter = ('status', 'payment_method', 'date_payment')
    search_fields = ('participant__first_name', 'participant__last_name', 'transaction_id')

@admin.register(Logistics)
class LogisticsAdmin(admin.ModelAdmin):
    list_display = ('participant', 'arrival_datetime', 'hotel_name', 'room_number')
    search_fields = ('participant__first_name', 'participant__last_name', 'hotel_name')
