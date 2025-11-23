from django.contrib import admin
from .models import OnlineSatis


@admin.register(OnlineSatis)
class OnlineSatisAdmin(admin.ModelAdmin):
    list_display = ("id", "satis_sayisi")

