from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout_view'),
    path('payment/<str:method>/', views.process_payment, name='process_payment'),
    
    # Custom Web Admin Dashboard
    path('gestion/', views.admin_dashboard, name='custom_admin_dashboard'),
    path('gestion/participants/', views.admin_participants, name='custom_admin_participants'),
    path('gestion/paiement/<int:payment_id>/valider/', views.admin_validate_payment, name='admin_validate_payment'),
    
    # Participants CRUD
    path('gestion/participants/<uuid:id>/supprimer/', views.admin_participant_delete, name='admin_participant_delete'),
    
    # Logistique CRUD
    path('gestion/logistique/', views.admin_logistics, name='custom_admin_logistics'),
    path('gestion/logistique/<int:id>/attribuer/', views.admin_logistics_assign, name='admin_logistics_assign'),
]
