# Generated manually

from django.db import migrations, models


def set_default_profil_fotografi(apps, schema_editor):
    """
    Mevcut kayıtlar için varsayılan profil fotoğrafı ayarla (eğer null ise)
    EvcilHayvan bağlantısı varsa ondan al
    """
    HayvanProfili = apps.get_model('ilan', 'HayvanProfili')
    
    for profil in HayvanProfili.objects.filter(profil_fotografi__isnull=True):
        # EvcilHayvan'dan almayı dene
        if profil.evcil_hayvan_id:
            try:
                EvcilHayvan = apps.get_model('anahtarlik', 'EvcilHayvan')
                evcil_hayvan = EvcilHayvan.objects.get(id=profil.evcil_hayvan_id)
                if evcil_hayvan.resim:
                    profil.profil_fotografi = evcil_hayvan.resim
                    profil.save(update_fields=['profil_fotografi'])
                    continue
            except:
                pass
        
        # Eğer EvcilHayvan'dan alamazsa, bu kayıt silinmeli veya varsayılan bir resim atanmalı
        # Şimdilik kayıtları olduğu gibi bırakıyoruz (migration başarısız olursa manuel müdahale gerekir)
        pass


def reverse_set_default_profil_fotografi(apps, schema_editor):
    """Geri alma işlemi - gerekli değil"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ilan', '0015_make_dogum_tarihi_required'),
    ]

    operations = [
        # Önce mevcut null kayıtları güncelle
        migrations.RunPython(set_default_profil_fotografi, reverse_set_default_profil_fotografi),
        
        # Sonra field'ı required yap
        migrations.AlterField(
            model_name='hayvanprofili',
            name='profil_fotografi',
            field=models.ImageField(upload_to='hayvan_profilleri/', verbose_name='Profil Fotoğrafı'),
        ),
    ]
