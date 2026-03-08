from django.http import JsonResponse
from .models import Banner


def banner_carousel_api(request):
    banners = Banner.objects.all()
    banners_data = [
        {"banner_title": banner.banner_title, "banner_image": banner.banner_image.url}
        for banner in banners
    ]
    return JsonResponse(banners_data, safe=False)
