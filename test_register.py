import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "teranga.settings")
django.setup()

from django.test import Client
from core.models import Participant, Club

club = Club.objects.first()
client = Client()
response = client.post('/register/', {
    'first_name': 'Test',
    'last_name': 'User',
    'email': 'testuser123@example.com',
    'telephone': '123456789',
    'whatsapp': '123456789',
    'pays': 'Senegal',
    'district': '9101',
    'club': club.id if club else '1',
    'type_participant': 'participant',
    'password': 'testpassword123',
    'payment_plan': 'comptant',
})

print("Status code:", response.status_code)
if response.status_code == 302:
    print("Redirect to:", response.url)
else:
    print("Form errors:", response.context.get('form').errors if response.context else "No context")

participant = Participant.objects.filter(email='testuser123@example.com').first()
if participant:
    print("Participant created. is_active:", participant.is_active, "otp:", participant.otp_code)
    
    # test verify_otp
    session = client.session
    session['verification_user_id'] = str(participant.id)
    session.save()
    response2 = client.post('/verify-otp/', {'otp': participant.otp_code})
    print("Verify OTP status:", response2.status_code)
    if response2.status_code == 302:
        print("Redirect after OTP:", response2.url)
else:
    print("Participant NOT created.")
