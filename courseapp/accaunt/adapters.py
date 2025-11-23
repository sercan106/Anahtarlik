from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib import messages
from django.shortcuts import redirect
from allauth.exceptions import ImmediateHttpResponse


class RequireTagAdapter(DefaultAccountAdapter):
    """
    Yeni kayıtların açılması için 'etiket_id' session anahtarını zorunlu kılar.
    Böylece adminin ürettiği etiket seri numarası girilmeden hesap açılamaz.
    """

    def is_open_for_signup(self, request):
        try:
            return bool(request and request.session.get('etiket_id'))
        except Exception:
            return False


class RequireTagSocialAdapter(DefaultSocialAccountAdapter):
    """
    Sosyal (Google) ile ilk kez kayıt olurken 'etiket_id' zorunlu.
    Mevcut kullanıcıların sosyal girişine engel olmaz; sadece yeni kayıtları kısıtlar.
    """

    def is_open_for_signup(self, request, sociallogin):
        try:
            # Eğer kullanıcı zaten mevcutsa (email eşleşmesi/bağlantı), signup sayılmaz.
            if sociallogin.is_existing:
                return True
            return bool(request and request.session.get('etiket_id'))
        except Exception:
            return False

    def pre_social_login(self, request, sociallogin):
        # Etiket yoksa yönlendir ve bilgilendir
        if not sociallogin.is_existing and not request.session.get('etiket_id'):
            messages.error(request, 'Önce etiket seri numarasını doğrulamanız gerekir.')
            raise ImmediateHttpResponse(redirect('step_1_check_tag'))
