# accaunt/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('guest/register/', views.guest_register, name='guest_register'),
    path('guest/panel/', views.guest_dashboard, name='guest_dashboard'),
    path('guest/profil-duzenle/', views.misafir_profil_duzenle, name='misafir_profil_duzenle'),
    path('guest/etiket-aktivasyon/', views.guest_activate_tag, name='guest_activate_tag'),
    path('guest/etiket-aktivasyon/hayvan/', views.guest_activate_pet, name='guest_activate_pet'),
    path('guest/etiket-aktivasyon/sahip/', views.guest_activate_owner, name='guest_activate_owner'),


    # 👇 Bu satır şablondaki {% url 'user_register' %} için gerekli!
    path('register/', views.step_1_check_tag, name='user_register'),
    
    # Künye aktivasyon (login olmayan kullanıcılar için)
    path('künye-aktivasyon/', views.künye_aktivasyon_adim1, name='künye_aktivasyon'),
    path('künye-aktivasyon/telefon/', views.künye_aktivasyon_adim2, name='künye_aktivasyon_adim2'),
    path('künye-aktivasyon/hayvan/', views.künye_aktivasyon_adim3, name='künye_aktivasyon_adim3'),

    path('register/step-1/', views.step_1_check_tag, name='step_1_check_tag'),
    path('register/step-2/', views.step_2_pet_info, name='step_2_pet_info'),
    path('register/step-3/', views.step_3_owner_info, name='step_3_owner_info'),
    path('register/step-4/', views.step_4_complete, name='step_4_complete'),
    path('register/districts/', views.districts_for_city, name='districts_for_city'),
    path('register/breeds/', views.breeds_for_species, name='breeds_for_species'),

    # Profil oluşturma
    path('veteriner-profil-olustur/', views.veteriner_profil_olustur, name='veteriner_profil_olustur'),
    path('petshop-profil-olustur/', views.petshop_profil_olustur, name='petshop_profil_olustur'),

    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='accaunt/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='accaunt/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accaunt/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accaunt/password_reset_complete.html'), name='password_reset_complete'),
]

