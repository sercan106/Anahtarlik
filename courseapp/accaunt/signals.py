from django.dispatch import receiver
from django.contrib.auth import get_user_model
from allauth.account.signals import user_signed_up, user_logged_in

from anahtarlik.models import Sahip


User = get_user_model()


def _ensure_owner(user: User) -> None:
    try:
        Sahip.objects.get_or_create(kullanici=user)
    except Exception:
        pass


@receiver(user_signed_up)
def on_user_signed_up(request, user, **kwargs):
    _ensure_owner(user)


@receiver(user_logged_in)
def on_user_logged_in(request, user, **kwargs):
    _ensure_owner(user)

