import logging
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from anahtarlik.dictionaries import Il, Ilce

logger = logging.getLogger(__name__)


@require_GET  # GET request olduğu için CSRF koruması gerekmez
def districts_for_province(request):
    """
    Standart İl-İlçe API Endpoint
    Tüm projede kullanılır.
    Response format: [{"id": 1, "ad": "İlçe Adı"}, ...]
    """
    il_id = request.GET.get("il_id")
    
    logger.debug(f"API Request - il_id: {il_id}")
    
    if not il_id:
        logger.warning("API Response - No il_id provided")
        return JsonResponse([], safe=False)
    
    try:
        il_id = int(il_id)
    except (TypeError, ValueError):
        logger.warning(f"API Response - Invalid il_id: {il_id}")
        return JsonResponse([], safe=False)

    try:
        # Eğer hiç il verisi yoksa örnek veri oluştur
        if Il.objects.count() == 0:
            logger.info("No il data found, creating sample data...")
            istanbul = Il.objects.create(ad="İstanbul")
            Ilce.objects.create(il=istanbul, ad="Adalar")
            Ilce.objects.create(il=istanbul, ad="Arnavutköy")
            Ilce.objects.create(il=istanbul, ad="Ataşehir")
            Ilce.objects.create(il=istanbul, ad="Avcılar")
            Ilce.objects.create(il=istanbul, ad="Bağcılar")
            Ilce.objects.create(il=istanbul, ad="Bahçelievler")
            Ilce.objects.create(il=istanbul, ad="Bakırköy")
            Ilce.objects.create(il=istanbul, ad="Başakşehir")
            Ilce.objects.create(il=istanbul, ad="Bayrampaşa")
            Ilce.objects.create(il=istanbul, ad="Beşiktaş")
            Ilce.objects.create(il=istanbul, ad="Beykoz")
            Ilce.objects.create(il=istanbul, ad="Beylikdüzü")
            Ilce.objects.create(il=istanbul, ad="Beyoğlu")
            Ilce.objects.create(il=istanbul, ad="Büyükçekmece")
            Ilce.objects.create(il=istanbul, ad="Çatalca")
            Ilce.objects.create(il=istanbul, ad="Çekmeköy")
            Ilce.objects.create(il=istanbul, ad="Esenler")
            Ilce.objects.create(il=istanbul, ad="Esenyurt")
            Ilce.objects.create(il=istanbul, ad="Eyüpsultan")
            Ilce.objects.create(il=istanbul, ad="Fatih")
            Ilce.objects.create(il=istanbul, ad="Gaziosmanpaşa")
            Ilce.objects.create(il=istanbul, ad="Güngören")
            Ilce.objects.create(il=istanbul, ad="Kadıköy")
            Ilce.objects.create(il=istanbul, ad="Kağıthane")
            Ilce.objects.create(il=istanbul, ad="Kartal")
            Ilce.objects.create(il=istanbul, ad="Küçükçekmece")
            Ilce.objects.create(il=istanbul, ad="Maltepe")
            Ilce.objects.create(il=istanbul, ad="Pendik")
            Ilce.objects.create(il=istanbul, ad="Sancaktepe")
            Ilce.objects.create(il=istanbul, ad="Sarıyer")
            Ilce.objects.create(il=istanbul, ad="Silivri")
            Ilce.objects.create(il=istanbul, ad="Sultanbeyli")
            Ilce.objects.create(il=istanbul, ad="Sultangazi")
            Ilce.objects.create(il=istanbul, ad="Şile")
            Ilce.objects.create(il=istanbul, ad="Şişli")
            Ilce.objects.create(il=istanbul, ad="Tuzla")
            Ilce.objects.create(il=istanbul, ad="Ümraniye")
            Ilce.objects.create(il=istanbul, ad="Üsküdar")
            Ilce.objects.create(il=istanbul, ad="Zeytinburnu")
            logger.info("Sample data created!")
        
        districts = list(
            Ilce.objects.filter(il_id=il_id)
            .order_by("ad")
            .values("id", "ad")
        )
        logger.debug(f"API Response - Found {len(districts)} districts for il_id {il_id}")
        return JsonResponse(districts, safe=False)
    except Exception as e:
        logger.error(f"API Error - {str(e)}", exc_info=True)
        return JsonResponse({"error": "Internal server error"}, status=500)
