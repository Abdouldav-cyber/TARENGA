from django.urls import path
from . import views
from . import exports

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('verify-otp/', views.verify_otp, name='verify_otp'),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout_view'),
    path('payment/<str:method>/', views.process_payment, name='process_payment'),
    
    # APIs
    path('api/check_participant/', views.check_participant_api, name='check_participant_api'),
    path('api/get_clubs/', views.get_clubs_api, name='get_clubs_api'),
    
    # Donations
    path('donation/', views.make_donation, name='make_donation'),
    path('programme/', views.programme, name='programme'),
    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),
    
    # Brand Center
    path('brand-center/', views.brand_center, name='brand_center'),
    path('brand-center/post/create/', views.create_post, name='create_post'),
    path('brand-center/post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('brand-center/post/<int:post_id>/comment/', views.add_comment, name='add_comment'),

    # Custom Web Admin Dashboard
    path('gestion/', views.admin_dashboard, name='custom_admin_dashboard'),
    path('gestion/participants/', views.admin_participants, name='custom_admin_participants'),
    path('gestion/paiement/<int:payment_id>/valider/', views.admin_validate_payment, name='admin_validate_payment'),
    
    # Participants CRUD
    path('gestion/participants/<uuid:id>/supprimer/', views.admin_participant_delete, name='admin_participant_delete'),
    
    # Custom Admin New Modules
    path('gestion/clubs/', views.custom_admin_clubs, name='custom_admin_clubs'),
    path('gestion/dons/', views.custom_admin_dons, name='custom_admin_dons'),
    path('gestion/taxes/', views.custom_admin_taxes, name='custom_admin_taxes'),
    path('gestion/brand-center/', views.custom_admin_posts, name='custom_admin_posts'),
    path('gestion/packs/', views.custom_admin_packs, name='custom_admin_packs'),
    path('gestion/programme/', views.custom_admin_programme, name='custom_admin_programme'),
    
    # Logistique CRUD
    path('gestion/logistique/', views.admin_logistics, name='custom_admin_logistics'),
    path('gestion/logistique/<int:id>/attribuer/', views.admin_logistics_assign, name='admin_logistics_assign'),

    # Exportations CSV
    path('gestion/export/participants/<str:event_type>/', exports.export_participants_csv, name='export_participants'),
    path('gestion/export/logistique/', exports.export_logistics_csv, name='export_logistics'),
    path('gestion/export/clubs/', exports.export_clubs_csv, name='export_clubs'),
    path('gestion/export/dons/', exports.export_dons_csv, name='export_dons'),
    path('gestion/export/taxes/', exports.export_taxes_csv, name='export_taxes'),
]
