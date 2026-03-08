from django.http import JsonResponse
from django.db.models import Q
from .models import Place


def place_list_api(request):
    search_query = request.GET.get("q", "")
    if search_query:
        places = Place.objects.filter(Q(place_name__icontains=search_query))
    else:
        places = Place.objects.all()

    places_data = [
        {"place_id": str(place.place_id), "place_name": place.place_name}
        for place in places
    ]
    return JsonResponse(places_data, safe=False)
