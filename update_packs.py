from core.models import EventPack

def update_packs():
    desc_standard = "Accès complet aux conférences-Déjeuners inclus-Kit de bienvenue-Accès au village"
    desc_premium = "Tout le Pack Standard-Accès au Dîner de Gala de clôture-Places réservées aux conférences"
    desc_vip = "Tout le Pack Premium-Hébergement en Hôtel 5 étoiles-Navette privée aéroport/hôtel-Accès exclusif au salon VIP"

    for pack in EventPack.objects.all():
        if "Standard" in pack.name:
            pack.description = desc_standard
        elif "Premium" in pack.name:
            pack.description = desc_premium
        elif "VIP" in pack.name:
            pack.description = desc_vip
        pack.save()
        print(f"Updated: {pack.name} for event {pack.event.event_type}")

update_packs()
