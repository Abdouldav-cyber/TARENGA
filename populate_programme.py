import os
import django
from datetime import date, time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'teranga.settings')
django.setup()

from core.models import Event, EventDay, EventSession

# Get or create an event
event = Event.objects.first()
if not event:
    event = Event.objects.create(
        name="Téranga 2027", 
        event_type="rotary", 
        start_date="2027-04-20", 
        end_date="2027-04-23"
    )

# Day 1
day1, _ = EventDay.objects.get_or_create(
    event=event,
    date=date(2027, 4, 20),
    defaults={'title': "Arrivée et Cérémonie d'Ouverture"}
)

EventSession.objects.get_or_create(
    day=day1,
    title="Accueil des délégations & Remise des badges",
    defaults={
        'start_time': time(8, 0),
        'end_time': time(12, 0),
        'location': "Hall Principal",
        'description': "Accueil chaleureux, récupération des packs et installation."
    }
)

EventSession.objects.get_or_create(
    day=day1,
    title="Cérémonie officielle d'ouverture",
    defaults={
        'start_time': time(15, 0),
        'end_time': time(18, 0),
        'location': "Grand Auditorium",
        'speakers': "Gouverneur du District, Représentant RI",
        'description': "Discours d'ouverture, hymnes et parade des drapeaux."
    }
)

# Day 2
day2, _ = EventDay.objects.get_or_create(
    event=event,
    date=date(2027, 4, 21),
    defaults={'title': "Ateliers et Formations"}
)

EventSession.objects.get_or_create(
    day=day2,
    title="Plénière : L'Avenir du Rotary en Afrique",
    defaults={
        'start_time': time(9, 0),
        'end_time': time(10, 30),
        'location': "Salle A",
        'speakers': "Comité Stratégique",
    }
)

EventSession.objects.get_or_create(
    day=day2,
    title="Dîner de Gala & Remise des Prix",
    defaults={
        'start_time': time(20, 0),
        'end_time': time(23, 59),
        'location': "Hôtel Teranga Plage",
        'description': "Tenue de soirée exigée. Célébration des clubs les plus performants."
    }
)

print("Programme généré avec succès !")
