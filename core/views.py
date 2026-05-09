from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
import random
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum
from django.core.paginator import Paginator
from .models import Payment, Logistics, Event, Participant, Post, PostLike, Comment, Donation, Club, HomepageContent, EventPack, EventDay, EventSession, ClubTax
from django.contrib import messages
from .forms import ParticipantRegistrationForm

def home(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('core:custom_admin_dashboard')
        else:
            return redirect('core:dashboard')
            
    content = HomepageContent.objects.first()
    context = {'homepage_content': content}
    return render(request, 'home.html', context)


def register(request):
    event_type = request.GET.get('event', 'rotary')
    event_obj = Event.objects.filter(event_type=event_type).first()
    clubs = Club.objects.filter(is_active=True)
    
    # Auto-création de l'événement s'il n'existe pas encore
    if not event_obj:
        event_obj = Event.objects.create(
            name=f"Événement {event_type.title()}", 
            event_type=event_type, 
            start_date='2027-01-01', 
            end_date='2027-01-05'
        )
    
    if request.method == 'POST':
        email = request.POST.get('email')
        whatsapp = request.POST.get('whatsapp')
        is_procuration = request.POST.get('is_procuration') == 'on'
        
        # Inscription d'un nouveau participant ou procuration
        if not request.user.is_authenticated or is_procuration:
            if Participant.objects.filter(email=email).exists():
                messages.error(request, "Un participant avec cet email est déjà inscrit.")
                return redirect(f"/register/?event={event_type}")
            if whatsapp and Participant.objects.filter(whatsapp=whatsapp).exists():
                messages.error(request, "Un participant avec ce numéro WhatsApp est déjà inscrit.")
                return redirect(f"/register/?event={event_type}")
            
            form = ParticipantRegistrationForm(request.POST, request.FILES)
        else:
            # Mise à jour de l'utilisateur connecté (inscription à un événement supplémentaire)
            form = ParticipantRegistrationForm(request.POST, request.FILES, instance=request.user)

        if form.is_valid():
            participant = form.save(commit=False)
            
            participant.is_procuration = is_procuration
            pack_id = request.POST.get('pack')
            if pack_id:
                participant.pack_id = pack_id
                
            participant.username = form.cleaned_data['email']
            participant.event_choice = event_obj
            
            if not request.user.is_authenticated or is_procuration:
                password = request.POST.get('password')
                if password:
                    participant.set_password(password)
                else:
                    participant.set_unusable_password() 
                
                # Setup OTP for new accounts
                if not request.user.is_authenticated:
                    participant.is_active = False
                    participant.otp_code = str(random.randint(100000, 999999))
            
            participant.save()

            payment_plan = request.POST.get('payment_plan', 'comptant')
            # Obtenir l'objet pack complet pour lire le prix exact
            pack_price = participant.pack.price_fcfa if participant.pack else 100000
            Payment.objects.create(
                participant=participant, 
                amount_paid=0, 
                amount_total=pack_price,
                payment_plan=payment_plan
            )
            
            hotel_name = request.POST.get('hotel_name', '')
            if not hasattr(participant, 'logistics'):
                Logistics.objects.create(participant=participant, hotel_name=hotel_name)
            else:
                participant.logistics.hotel_name = hotel_name
                participant.logistics.save()

            if not request.user.is_authenticated and not is_procuration:
                # Send OTP email
                subject = "Vérification de votre compte Teranga 2027"
                message = f"Bonjour {participant.first_name},\n\nVotre code de vérification est : {participant.otp_code}\n\nMerci de vous inscrire à Teranga Experience 2027 !"
                try:
                    send_mail(
                        subject,
                        message,
                        settings.EMAIL_HOST_USER,
                        [participant.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    print(f"Erreur d'envoi d'email: {e}")
                
                request.session['verification_user_id'] = str(participant.id)
                return redirect('core:verify_otp')
            else:
                messages.success(request, "🎉 Inscription validée ! Bienvenue à Teranga 2027.")
                return redirect('core:dashboard')
    else:
        # GET request
        if request.user.is_authenticated:
            # Pré-remplissage pour l'utilisateur connecté
            form = ParticipantRegistrationForm(instance=request.user)
        else:
            form = ParticipantRegistrationForm()
        
    # Récupérer les packs
    packs = EventPack.objects.filter(event=event_obj) if event_obj else []

    context = {
        'form': form,
        'event_type': event_type,
        'clubs': clubs,
        'packs': packs,
    }
    return render(request, 'register.html', context)

def check_participant_api(request):
    identifier = request.GET.get('identifier', '').strip()
    event_type = request.GET.get('event', '')
    
    if not identifier:
        return JsonResponse({'status': 'error', 'message': 'Identifiant manquant'})
        
    from django.db.models import Q
    participant = Participant.objects.filter(Q(email=identifier) | Q(whatsapp=identifier) | Q(telephone=identifier)).first()
    
    if participant:
        if participant.event_choice and participant.event_choice.event_type == event_type:
            return JsonResponse({
                'exists': True, 
                'registered_for_event': True,
                'message': f"Un participant avec cet identifiant ({identifier}) est déjà inscrit à cet événement."
            })
        else:
            return JsonResponse({
                'exists': True,
                'registered_for_event': False,
                'message': "Un compte existe déjà. Vous pouvez vous connecter pour pré-remplir vos informations."
            })
            
    return JsonResponse({'exists': False})

def get_clubs_api(request):
    pays = request.GET.get('pays', '')
    district = request.GET.get('district', '')
    
    clubs = Club.objects.filter(is_active=True)
    if pays:
        # Assuming we might want to filter by country if the field exists in Club model.
        # Actually Club has `country` and `city`.
        # Map 'Senegal' -> 'Sénégal', etc, or just do case insensitive match.
        pass # Depending on how you store them. But let's check exact match if provided.
        # clubs = clubs.filter(country__icontains=pays)
        
    # Since Club model only has country, not district explicitly (unless it's in another field),
    # For now, let's just return all clubs or filter if you add district to Club.
    # Currently Club model has: name, club_type, country, city. No district.
    # So we'll filter by country if provided.
    if pays:
        pays_mapping = {
            'Senegal': 'Sénégal', 'Mali': 'Mali', 'CoteIvoire': "Côte d'Ivoire", 'BurkinaFaso': 'Burkina Faso'
        }
        country_name = pays_mapping.get(pays, pays)
        clubs = clubs.filter(country__icontains=country_name)
        
    clubs_data = list(clubs.values('id', 'name', 'country'))
    return JsonResponse({'clubs': clubs_data})

def verify_otp(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        return redirect('core:home')
        
    try:
        participant = Participant.objects.get(id=user_id)
    except Participant.DoesNotExist:
        return redirect('core:home')
        
    if request.method == 'POST':
        otp_entered = request.POST.get('otp', '').strip()
        if otp_entered == participant.otp_code:
            participant.is_active = True
            participant.is_email_verified = True
            participant.otp_code = None
            participant.save()
            
            # Connect the user
            login(request, participant, backend='django.contrib.auth.backends.ModelBackend')
            del request.session['verification_user_id']
            
            messages.success(request, "✅ Compte vérifié avec succès ! Bienvenue à Teranga 2027.")
            return redirect('core:dashboard')
        else:
            messages.error(request, "❌ Le code OTP est incorrect. Veuillez réessayer.")
            
    return render(request, 'verify_otp.html', {'email': participant.email})

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
# MODULE DONS
# ==========================================
def make_donation(request):
    clubs = Club.objects.filter(is_active=True)
    if request.method == 'POST':
        amount = request.POST.get('amount')
        beneficiary_type = request.POST.get('beneficiary_type')
        message = request.POST.get('message')
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        
        donation = Donation(
            amount=amount,
            beneficiary_type=beneficiary_type,
            message=message,
            is_anonymous=is_anonymous
        )
        
        if request.user.is_authenticated:
            donation.donateur_user = request.user
            
        if beneficiary_type == 'club':
            club_id = request.POST.get('beneficiary_club')
            if club_id:
                donation.beneficiary_club_id = club_id
        elif beneficiary_type in ['personne', 'organisation']:
            donation.beneficiary_name = request.POST.get('beneficiary_name')
            
        donation.save()
        messages.success(request, f"Merci beaucoup pour votre don de {amount} FCFA !")
        return redirect('core:home')
        
    context = {
        'clubs': clubs
    }
    return render(request, 'donation.html', context)

def programme(request):
    days = EventDay.objects.prefetch_related('sessions').all()
    context = {'days': days}
    return render(request, 'programme.html', context)

@login_required(login_url='/login/')
def notifications_view(request):
    notifs = request.user.notifications.all()
    # Marquer comme lu
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications.html', {'notifications': notifs})

# ==========================================
# BRAND CENTER (RESEAU SOCIAL)
# ==========================================
def brand_center(request):
    posts = Post.objects.all().select_related('author').prefetch_related('comments', 'comments__author', 'likes')
    context = {
        'posts': posts,
    }
    return render(request, 'brand_center.html', context)

@login_required(login_url='/login/')
def create_post(request):
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            Post.objects.create(author=request.user, text=text)
            messages.success(request, "Votre publication a été ajoutée !")
    return redirect('core:brand_center')

@login_required(login_url='/login/')
def like_post(request, post_id):
    post = Post.objects.get(id=post_id)
    like, created = PostLike.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
        post.likes_count -= 1
    else:
        post.likes_count += 1
    post.save()
    return redirect('core:brand_center')

@login_required(login_url='/login/')
def add_comment(request, post_id):
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            post = Post.objects.get(id=post_id)
            Comment.objects.create(post=post, author=request.user, text=text)
            post.comments_count += 1
            post.save()
            messages.success(request, "Commentaire ajouté !")
    return redirect('core:brand_center')

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
    
    total_dons = Donation.objects.filter(status='paye').aggregate(Sum('amount'))['amount__sum'] or 0
    total_posts = Post.objects.count()
    
    context = {
        'total_participants': total_participants,
        'total_rotary': total_rotary,
        'total_rotaract': total_rotaract,
        'chiffre_affaire': chiffre_affaire,
        'en_attente': en_attente,
        'total_dons': total_dons,
        'total_posts': total_posts,
    }
    return render(request, 'custom_admin/dashboard.html', context)

@user_passes_test(is_admin, login_url='/')
def admin_participants(request):
    all_payments = Payment.objects.exclude(participant__is_superuser=True).select_related('participant', 'participant__event_choice')
    
    rotary_payments = all_payments.filter(participant__event_choice__event_type='rotary')
    rotaract_payments = all_payments.filter(participant__event_choice__event_type='rotaract')
    
    paginator_rotary = Paginator(rotary_payments, 10)
    page_rotary = request.GET.get('page_rotary')
    rotary_obj = paginator_rotary.get_page(page_rotary)

    paginator_rotaract = Paginator(rotaract_payments, 10)
    page_rotaract = request.GET.get('page_rotaract')
    rotaract_obj = paginator_rotaract.get_page(page_rotaract)
    
    context = {
        'rotary_payments': rotary_payments, # Keep original querysets for counts if needed
        'rotaract_payments': rotaract_payments,
        'rotary_obj': rotary_obj,
        'rotaract_obj': rotaract_obj,
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
    paginator = Paginator(logistics_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'logistics_list': logistics_list, 'page_obj': page_obj}
    return render(request, 'custom_admin/logistics.html', context)

@user_passes_test(is_admin, login_url='/')
def custom_admin_clubs(request):
    clubs = Club.objects.all().order_by('-creation_date')
    paginator = Paginator(clubs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'clubs': clubs, 'page_obj': page_obj}
    return render(request, 'custom_admin/clubs.html', context)

@user_passes_test(is_admin, login_url='/')
def custom_admin_dons(request):
    dons = Donation.objects.all().order_by('-created_at')
    paginator = Paginator(dons, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'dons': dons, 'page_obj': page_obj}
    return render(request, 'custom_admin/dons.html', context)

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

@user_passes_test(is_admin, login_url='/')
def custom_admin_taxes(request):
    taxes = ClubTax.objects.all().select_related('club', 'mandat')
    paginator = Paginator(taxes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'custom_admin/taxes.html', {'taxes': taxes, 'page_obj': page_obj})

@user_passes_test(is_admin, login_url='/')
def custom_admin_posts(request):
    posts = Post.objects.all().select_related('author').order_by('-created_at')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'custom_admin/posts.html', {'posts': posts, 'page_obj': page_obj})

@user_passes_test(is_admin, login_url='/')
def custom_admin_packs(request):
    packs = EventPack.objects.all().select_related('event')
    paginator = Paginator(packs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'custom_admin/packs.html', {'packs': packs, 'page_obj': page_obj})

@user_passes_test(is_admin, login_url='/')
def custom_admin_programme(request):
    days = EventDay.objects.prefetch_related('sessions').all().order_by('date')
    paginator = Paginator(days, 5) # 5 days per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'custom_admin/programme.html', {'days': days, 'page_obj': page_obj})
