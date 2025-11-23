# Generated manually

from django.db import migrations, models
from datetime import date


def set_default_dogum_tarihi(apps, schema_editor):
    """
    Mevcut kayıtlar için varsayılan doğum tarihi ayarla (eğer null ise)
    EvcilHayvan bağlantısı varsa ondan al, yoksa bugünden 1 yıl öncesini kullan
    """
    HayvanProfili = apps.get_model('ilan', 'HayvanProfili')
    
    for profil in HayvanProfili.objects.filter(dogum_tarihi__isnull=True):
        # Önce evcil_hayvan'dan almayı dene
        if profil.evcil_hayvan_id:
            try:
                EvcilHayvan = apps.get_model('anahtarlik', 'EvcilHayvan')
                evcil_hayvan = EvcilHayvan.objects.get(id=profil.evcil_hayvan_id)
                if evcil_hayvan.dogum_tarihi:
                    profil.dogum_tarihi = evcil_hayvan.dogum_tarihi
                    profil.save(update_fields=['dogum_tarihi'])
                    continue
            except:
                pass
        
        # EvcilHayvan'dan alamazsa, bugünden 1 yıl öncesini varsayılan olarak kullan
        from datetime import timedelta
        profil.dogum_tarihi = date.today() - timedelta(days=365)
        profil.save(update_fields=['dogum_tarihi'])


def reverse_set_default_dogum_tarihi(apps, schema_editor):
    """Geri alma işlemi - gerekli değil"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ilan', '0014_change_yas_to_dogum_tarihi'),
    ]

    operations = [
        # Önce mevcut null kayıtları güncelle
        migrations.RunPython(set_default_dogum_tarihi, reverse_set_default_dogum_tarihi),
        
        # Sonra field'ı required yap
        migrations.AlterField(
            model_name='hayvanprofili',
            name='dogum_tarihi',
            field=models.DateField(help_text='Hayvanın doğum tarihi', verbose_name='Doğum Tarihi'),
        ),
    ]
