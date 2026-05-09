from core.models import Event, EventPack

def run():
    print("Populating default packs...")
    events = Event.objects.all()
    if not events.exists():
        # Create a dummy event if none exists so packs have an event to attach to
        print("No events found. Creating default Rotary Event.")
        event = Event.objects.create(name="Téranga 2027 (Rotary)", event_type="rotary", start_date="2027-05-01", end_date="2027-05-05")
    else:
        event = events.first()

    packs_data = [
        {"name": "Pack Standard", "price_fcfa": 100000, "description": "Accès aux conférences et déjeuners de base."},
        {"name": "Pack Premium", "price_fcfa": 150000, "description": "Accès conférences, déjeuners, et dîner de gala."},
        {"name": "Pack VIP", "price_fcfa": 250000, "description": "Expérience complète : Hôtel 5 étoiles, navette privée, accès VIP."},
    ]

    for data in packs_data:
        pack, created = EventPack.objects.get_or_create(
            event=event,
            name=data['name'],
            defaults={'price_fcfa': data['price_fcfa'], 'description': data['description']}
        )
        if created:
            print(f"Created: {pack.name}")
        else:
            print(f"Already exists: {pack.name}")

run()
