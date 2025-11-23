from django.contrib.auth.models import User
from django.db import models


class MisafirProfil(models.Model):
    kullanici = models.OneToOneField(User, on_delete=models.CASCADE, related_name='misafir_profili')
    ad_soyad = models.CharField(max_length=150)
    telefon = models.CharField(max_length=15, unique=True)
    uyelik_sozlesmesi_onay = models.BooleanField(default=False)
    olusturulma = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Misafir Profil'
        verbose_name_plural = 'Misafir Profilleri'

    def __str__(self):
        return self.ad_soyad or self.kullanici.get_username()
