from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Participant, Event, Payment, Logistics, Club, Mandat, ClubTax, Donation, Post, Comment, EventPack, EventActivity, HomepageContent, EventDay, EventSession, Notification

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


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'club_type', 'country', 'city', 'is_active')
    list_filter = ('club_type', 'country', 'is_active')
    search_fields = ('name', 'city')


@admin.register(Mandat)
class MandatAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'start_year', 'end_year', 'is_active')
    list_filter = ('is_active',)


@admin.register(ClubTax)
class ClubTaxAdmin(admin.ModelAdmin):
    list_display = ('club', 'mandat', 'amount_expected', 'amount_paid', 'status', 'due_date')
    list_filter = ('status', 'mandat')
    search_fields = ('club__name',)

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('amount', 'status', 'beneficiary_type', 'donateur_user', 'created_at')
    list_filter = ('status', 'beneficiary_type')
    search_fields = ('donateur_user__username', 'beneficiary_name')

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'created_at', 'likes_count', 'comments_count')
    search_fields = ('author__username', 'text')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'created_at')
    search_fields = ('author__username', 'text')

@admin.register(EventPack)
class EventPackAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price_fcfa')
    list_filter = ('event',)

@admin.register(EventActivity)
class EventActivityAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price_fcfa', 'is_daily')
    list_filter = ('event', 'is_daily')

@admin.register(HomepageContent)
class HomepageContentAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'updated_at')

    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

class EventSessionInline(admin.TabularInline):
    model = EventSession
    extra = 1

@admin.register(EventDay)
class EventDayAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'event')
    list_filter = ('event',)
    inlines = [EventSessionInline]

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('participant', 'title', 'type_notif', 'is_read', 'created_at')
    list_filter = ('is_read', 'type_notif', 'created_at')
    search_fields = ('participant__email', 'title', 'message')
