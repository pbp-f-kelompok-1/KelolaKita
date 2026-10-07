from django.shortcuts import render
from main.models import Location

def landing_page(request):
    return render(request, "index.html")

def show_location(request):
    location_list = Location.objects.filter(is_active=True)
    locations = [
        {
            'name': loc.name,
            'address': loc.address,
            'latitude': float(loc.latitude),
            'longitude': float(loc.longitude),
        }
        for loc in location_list
    ]
    context = {
        "location_list": location_list,
        "locations": locations,
    }
    return render(request, "location.html", context)