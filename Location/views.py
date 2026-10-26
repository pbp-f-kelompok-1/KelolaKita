from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from Location.forms import LocationForm
from Location.models import Location


def show_location(request):
    location_list = Location.objects.filter(is_active=True)
    locations = [
        {
            'id': str(loc.id),
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
        "active_nav": "peta",
    }
    return render(request, "Location/location.html", context)


def create_location(request):
    form = LocationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Lokasi berhasil ditambahkan")
        return redirect("show_location")

    return render(request, "Location/location_form.html", {"name": "KelolaKita", "form": form, "active_nav": "peta"})


def delete_location(request, location_id):
    location = get_object_or_404(Location, pk=location_id)

    if request.method == "POST":
        location.delete()
        messages.success(request, "Lokasi berhasil dihapus!")
        return redirect("show_location")

    return redirect("show_location")


def location_detail(request, pk):
    loc = get_object_or_404(Location, pk=pk, is_active=True)
    return render(request, 'Location/location_detail.html', {'loc': loc, 'active_nav': 'peta'})
