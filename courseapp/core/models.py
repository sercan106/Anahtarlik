from django.db import models


class OnlineSatis(models.Model):
    """
    ONLINE kanalındaki toplam satış/adet sayaçlarını tutmak için basit model.
    Kod, sabit id=1 kaydı üzerinde artış yapıyor.
    """

    satis_sayisi = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Online Satış Sayacı"
        verbose_name_plural = "Online Satış Sayaçları"

    def __str__(self) -> str:
        return f"Online satış sayısı: {self.satis_sayisi}"

