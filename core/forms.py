from django import forms
from .models import Participant, Logistics, Event

class ParticipantRegistrationForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = [
            'first_name', 'last_name', 'email', 'whatsapp', 
            'district', 'pays', 'club', 'poste', 'type_participant'
        ]

class ParticipantEditForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['first_name', 'last_name', 'email', 'whatsapp', 'pays', 'district', 'club', 'poste', 'type_participant']
        widgets = { field: forms.TextInput(attrs={'class': 'glass-input'}) for field in ['first_name', 'last_name', 'whatsapp', 'pays', 'district', 'club', 'poste'] }
        widgets['email'] = forms.EmailInput(attrs={'class': 'glass-input'})
        widgets['type_participant'] = forms.Select(attrs={'class': 'glass-input'})

class LogisticsAssignForm(forms.ModelForm):
    class Meta:
        model = Logistics
        fields = ['arrival_datetime', 'transport_mode', 'hotel_name', 'room_number']
        labels = {
            'arrival_datetime': 'Date et heure d\'arrivée',
            'transport_mode': 'Mode de Transport',
            'hotel_name': 'Hôtel assigné',
            'room_number': 'Numéro de Chambre'
        }
        widgets = {
            'arrival_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'transport_mode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Vol AirSénégal ou Navette'}),
            'hotel_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'Hôtel'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: B-205'}),
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['name', 'event_type', 'start_date', 'end_date', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'glass-input'}),
            'event_type': forms.Select(attrs={'class': 'glass-input'}),
            'start_date': forms.DateInput(attrs={'class': 'glass-input', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'glass-input', 'type': 'date'}),
        }
