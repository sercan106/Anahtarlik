from django.db import models


class Tur(models.Model):
    ad = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["ad"]

    def __str__(self):
        return self.ad


class Irk(models.Model):
    tur = models.ForeignKey(Tur, on_delete=models.CASCADE, related_name="irklari")
    ad = models.CharField(max_length=120)

    class Meta:
        unique_together = ("tur", "ad")
        ordering = ["tur__ad", "ad"]
        verbose_name = "İrk"
        verbose_name_plural = "Irklar"

    def __str__(self):
        return f"{self.tur.ad} - {self.ad}"


class Il(models.Model):
    ad = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["ad"]

    def __str__(self):
        return self.ad


class Ilce(models.Model):
    il = models.ForeignKey(Il, on_delete=models.CASCADE, related_name="ilceler")
    ad = models.CharField(max_length=120)

    class Meta:
        unique_together = ("il", "ad")
        ordering = ["il__ad", "ad"]
        verbose_name = "İlçe"
        verbose_name_plural = "İlçeler"

    def __str__(self):
        return f"{self.ad} ({self.il.ad})"


class Mahalle(models.Model):
    ilce = models.ForeignKey(Ilce, on_delete=models.CASCADE, related_name="mahalleler")
    ad = models.CharField(max_length=150)

    class Meta:
        unique_together = ("ilce", "ad")
        ordering = ["ilce__il__ad", "ilce__ad", "ad"]
        verbose_name = "Mahalle"
        verbose_name_plural = "Mahalleler"

    def __str__(self):
        return f"{self.ad} ({self.ilce.ad}, {self.ilce.il.ad})"

