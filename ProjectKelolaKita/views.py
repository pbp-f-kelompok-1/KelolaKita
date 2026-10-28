from functools import wraps

from django.contrib import messages
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from Location.models import Location
from Location.forms import LocationForm


def staff_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse("admin:login"))
        if not (request.user.is_active and request.user.is_staff):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped



def landing_page(request):
    return render(request, "index.html")

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

@staff_required
@require_http_methods(["GET", "POST"])
def create_location(request) :
    form = LocationForm(request.POST or None)

    if request.method == "POST" and form.is_valid() :
        form.save()
        messages.success(request, "Lokasi berhasil ditambahkan")
        return redirect("show_location")

    return render(request, "Location/location_form.html", {"name": "KelolaKita", "form": form, "active_nav": "peta"})

@staff_required
@require_http_methods(["GET", "POST"])
def delete_location(request, location_id) :
    location = get_object_or_404(Location, pk=location_id)

    if request.method == "POST" :
        try:
            location.delete()
        except ProtectedError:
            messages.error(
                request,
                "Lokasi tidak bisa dihapus karena masih dipakai agenda atau catatan penyaluran.",
            )
            return redirect("show_location")
        messages.success(request, "Lokasi berhasil dihapus!")
        return redirect("show_location")

    return redirect("show_location")

def location_detail(request, pk):
    loc = get_object_or_404(Location, pk=pk, is_active=True)
    return render(request, 'Location/location_detail.html', {'loc': loc, 'active_nav': 'peta'})
