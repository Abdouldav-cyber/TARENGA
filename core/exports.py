import csv
import datetime
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from .models import Payment, Logistics, Club, Donation, ClubTax, Participant
from .views import is_admin

@user_passes_test(is_admin, login_url='/')
def export_participants_csv(request, event_type):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="participants_{event_type}_{datetime.date.today()}.csv"'
    
    # Encodage UTF-8 avec BOM pour Excel
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nom', 'Prénom', 'Email', 'WhatsApp', 'Pays', 'Club', 'Type', 'Pack', 'Plan Paiement', 'Total à Payer (FCFA)', 'Payé (FCFA)', 'Reste (FCFA)', 'Statut'])
    
    payments = Payment.objects.exclude(participant__is_superuser=True).select_related('participant', 'participant__event_choice', 'participant__pack', 'participant__club')
    payments = payments.filter(participant__event_choice__event_type=event_type)
    
    for payment in payments:
        p = payment.participant
        club_name = p.club.name if p.club else "-"
        pack_name = p.pack.name if p.pack else "-"
        reste = float(payment.amount_total) - float(payment.amount_paid)
        
        writer.writerow([
            p.last_name, p.first_name, p.email, p.whatsapp, p.pays, club_name,
            p.get_type_participant_display(), pack_name, payment.get_payment_plan_display(),
            payment.amount_total, payment.amount_paid, reste, payment.get_status_display()
        ])
    return response

@user_passes_test(is_admin, login_url='/')
def export_logistics_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="logistique_{datetime.date.today()}.csv"'
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Participant', 'Email', 'Club', 'Transport', 'Arrivée Prévue', 'Hôtel', 'Chambre', 'Billet Validé'])
    
    logistics = Logistics.objects.exclude(participant__is_superuser=True).select_related('participant', 'participant__club')
    
    for log in logistics:
        p = log.participant
        club_name = p.club.name if p.club else "-"
        # Check if ticket is validated (first payment paid)
        payment = p.payments.first()
        is_validated = "Oui" if payment and payment.status == 'paye' else "Non"
        arrival = log.arrival_datetime.strftime('%Y-%m-%d %H:%M') if log.arrival_datetime else "En attente"
        
        writer.writerow([
            f"{p.first_name} {p.last_name}", p.email, club_name, 
            log.transport_mode or "-", arrival, 
            log.hotel_name or "À attribuer", log.room_number or "-", is_validated
        ])
    return response

@user_passes_test(is_admin, login_url='/')
def export_clubs_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="clubs_{datetime.date.today()}.csv"'
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Nom du Club', 'Type', 'Pays', 'Ville', 'Statut'])
    
    for club in Club.objects.all():
        statut = "Actif" if club.is_active else "Inactif"
        writer.writerow([club.name, club.get_club_type_display(), club.country, club.city or "-", statut])
    return response

@user_passes_test(is_admin, login_url='/')
def export_dons_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="dons_{datetime.date.today()}.csv"'
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Date', 'Donateur', 'Type Bénéficiaire', 'Cible', 'Montant (FCFA)', 'Statut'])
    
    for don in Donation.objects.all().select_related('donateur_user', 'beneficiary_club'):
        if don.is_anonymous:
            donateur = "Anonyme"
        else:
            donateur = f"{don.donateur_user.first_name} {don.donateur_user.last_name}" if don.donateur_user else "Visiteur"
            
        if don.beneficiary_type == 'club':
            cible = don.beneficiary_club.name if don.beneficiary_club else "-"
        elif don.beneficiary_type in ['personne', 'organisation']:
            cible = don.beneficiary_name
        else:
            cible = "Lui-même"
            
        date_str = don.created_at.strftime('%Y-%m-%d %H:%M')
        writer.writerow([date_str, donateur, don.get_beneficiary_type_display(), cible, don.amount, don.get_status_display()])
    return response

@user_passes_test(is_admin, login_url='/')
def export_taxes_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="taxes_{datetime.date.today()}.csv"'
    response.write('\ufeff'.encode('utf8'))
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['Club', 'Mandat', 'Montant Attendu', 'Montant Payé', 'Date de paiement', 'Statut'])
    
    for t in ClubTax.objects.all().select_related('club', 'mandat'):
        date_str = t.due_date.strftime('%Y-%m-%d') if t.due_date else "-"
        writer.writerow([t.club.name, str(t.mandat), t.amount_expected, t.amount_paid, date_str, t.get_status_display()])
    return response
