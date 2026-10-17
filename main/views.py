from django.shortcuts import render
from main.models import Location
# Create your views here.


def landing_page(request):
    print("VIEW INDEX DIPANGGIL")   
    locations = [
        {
            'name': loc.name,
            'address': loc.address,
            'latitude': float(loc.latitude),
            'longitude': float(loc.longitude),
        }
        for loc in Location.objects.filter(is_active=True)[:100]
    ]
    return render(request, 'index.html', {'locations': locations})