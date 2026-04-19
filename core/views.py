from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from .models import Payment, Logistics, Event, Participant
from django.contrib import messages
from .forms import ParticipantRegistrationForm

def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('core:custom_admin_dashboard')
        else:
            return redirect('core:dashboard')
    return render(request, 'home.html')

def register(request):
    event_type = request.GET.get('event', 'rotary')
    event_obj = Event.objects.filter(event_type=event_type).first()
    
    # Auto-création de l'événement s'il n'existe pas encore
    if not event_obj:
        event_obj = Event.objects.create(
            name=f"Événement {event_type.title()}", 
            event_type=event_type, 
            start_date='2027-01-01', 
            end_date='2027-01-05'
        )
    
    if request.method == 'POST':
        form = ParticipantRegistrationForm(request.POST)
        if form.is_valid():
            participant = form.save(commit=False)
            # Nom d'utilisateur temporaire et Event
            participant.username = form.cleaned_data['email']
            participant.event_choice = event_obj
            participant.set_unusable_password() # Mot de passe non défini initialement
            participant.save()

            # Créer un enregistrement de paiement Vide par défaut
            Payment.objects.create(participant=participant, amount_paid=0, amount_total=100000) # 100 000 par ex
            # Créer un enregistrement logistique par défaut
            Logistics.objects.create(participant=participant)

            messages.success(request, "🎉 Inscription validée ! Bienvenue à Teranga 2027.")
            
            # Connexion automatique sans mot de passe (Backend requis)
            login(request, participant, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('core:dashboard')
    else:
        form = ParticipantRegistrationForm()
        
    context = {
        'form': form,
        'event_type': event_type,
    }
    return render(request, 'register.html', context)

def logout_view(request):
    logout(request)
    messages.success(request, "Vous avez été déconnecté en toute sécurité. À bientôt !")
    return redirect('core:home')

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('core:custom_admin_dashboard')
        return redirect('core:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password_or_whatsapp = request.POST.get('password')

        # 1. Tentative : SuperAdmin (Mot de passe classique)
        user = authenticate(request, username=email, password=password_or_whatsapp)
        if user is not None:
            login(request, user)
            if user.is_staff or user.is_superuser:
                return redirect('core:custom_admin_dashboard')
            return redirect('core:dashboard')
            
        # 2. Tentative : Participant (Email + Whatsapp car ils n'ont pas de mot de passe)
        try:
            participant = Participant.objects.get(email=email, whatsapp=password_or_whatsapp)
            login(request, participant, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('core:dashboard')
        except Participant.DoesNotExist:
            messages.error(request, "Erreur de connexion. Vérifiez votre Email et Mot de passe (ou Numéro WhatsApp).")

    return render(request, 'login.html')

@login_required(login_url='/')
def dashboard(request):
    participant = request.user
    payment = participant.payments.first()
    logistics = getattr(participant, 'logistics', None)
    
    context = {
        'participant': participant,
        'payment': payment,
        'logistics': logistics,
    }
    return render(request, 'dashboard.html', context)

@login_required(login_url='/')
def process_payment(request, method):
    # Simulation de l'API de paiement (Wave/OM/Paydunya)
    try:
        payment = request.user.payments.first()
        if payment and payment.status != 'paye':
            payment.status = 'paye'
            payment.amount_paid = payment.amount_total
            payment.save()
            
            # Déclenchement MAJEUR : Le paiement Client génère le QR Code
            if hasattr(request.user, 'logistics'):
                request.user.logistics.generate_qr_code()
                
            messages.success(request, f"Votre paiement via {method.upper()} a été approuvé avec succès ! Votre Billet a été débloqué.")
        return redirect('core:dashboard')
    except Exception as e:
        messages.error(request, "Une erreur est survenue lors de la communication avec l'API de paiement.")
        return redirect('core:dashboard')

# ==========================================
# VUES ADMINISTRATEUR WEB SUR-MESURE
# ==========================================
def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin, login_url='/')
def admin_dashboard(request):
    # AUTO-RÉPARATION : Si des participants ont pu s'inscrire avant la création de l'événement (La Faille)
    orphelins = Participant.objects.filter(event_choice__isnull=True, is_superuser=False)
    if orphelins.exists():
        fallback_event, _ = Event.objects.get_or_create(
            event_type='rotary',
            defaults={'name': 'Rotary Téranga 2027', 'start_date': '2027-01-01', 'end_date': '2027-01-05'}
        )
        orphelins.update(event_choice=fallback_event)

    total_participants = Participant.objects.exclude(is_superuser=True).count()
    total_rotary = Participant.objects.filter(event_choice__event_type='rotary', is_superuser=False).count()
    total_rotaract = Participant.objects.filter(event_choice__event_type='rotaract', is_superuser=False).count()
    
    # Calcul des paiements
    chiffre_affaire = Payment.objects.filter(status='paye').aggregate(Sum('amount_total'))['amount_total__sum'] or 0
    en_attente = Payment.objects.filter(status='non_paye').aggregate(Sum('amount_total'))['amount_total__sum'] or 0
    
    context = {
        'total_participants': total_participants,
        'total_rotary': total_rotary,
        'total_rotaract': total_rotaract,
        'chiffre_affaire': chiffre_affaire,
        'en_attente': en_attente,
    }
    return render(request, 'custom_admin/dashboard.html', context)

@user_passes_test(is_admin, login_url='/')
def admin_participants(request):
    all_payments = Payment.objects.exclude(participant__is_superuser=True).select_related('participant', 'participant__event_choice')
    
    rotary_payments = all_payments.filter(participant__event_choice__event_type='rotary')
    rotaract_payments = all_payments.filter(participant__event_choice__event_type='rotaract')
    
    context = {
        'rotary_payments': rotary_payments,
        'rotaract_payments': rotaract_payments,
    }
    return render(request, 'custom_admin/participants.html', context)

@user_passes_test(is_admin, login_url='/')
def admin_validate_payment(request, payment_id):
    payment = Payment.objects.get(id=payment_id)
    payment.status = 'paye'
    payment.amount_paid = payment.amount_total
    payment.save()
    
    # Le paiement est bon, on génère et délivre officiellement le billet / QR Code
    if hasattr(payment.participant, 'logistics'):
        payment.participant.logistics.generate_qr_code()
        
    messages.success(request, f"Paiement validé avec succès pour {payment.participant.first_name} !")
    return redirect('core:custom_admin_participants')

@user_passes_test(is_admin, login_url='/')
def admin_logistics(request):
    logistics_list = Logistics.objects.exclude(participant__is_superuser=True).select_related('participant')
    context = {'logistics_list': logistics_list}
    return render(request, 'custom_admin/logistics.html', context)

# ==========================================
# C.R.U.D ACTIONS (MODIFICATION ET SUPPRESSION)
# ==========================================
from django.urls import reverse
from .forms import LogisticsAssignForm

@user_passes_test(is_admin, login_url='/')
def admin_logistics_assign(request, id):
    logistics = Logistics.objects.get(id=id)
    if request.method == 'POST':
        form = LogisticsAssignForm(request.POST, instance=logistics)
        if form.is_valid():
            form.save()
            messages.success(request, f"Logistique mise à jour pour {logistics.participant.first_name}.")
            return redirect('core:custom_admin_logistics')
    else:
        form = LogisticsAssignForm(instance=logistics)
    
    context = {
        'form': form,
        'title': f"Attribuer Logistique : {logistics.participant.first_name}",
        'subtitle': "Veuillez renseigner les détails du voyage et de l'hôtel.",
        'cancel_url': reverse('core:custom_admin_logistics')
    }
    return render(request, 'custom_admin/form_page.html', context)

@user_passes_test(is_admin, login_url='/')
def admin_participant_delete(request, id):
    participant = Participant.objects.get(id=id)
    name = participant.first_name
    participant.delete()
    messages.success(request, f"Le participant {name} a été définitivement supprimé.")
    return redirect('core:custom_admin_participants')
