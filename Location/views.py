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
import json
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from Location.models import Location


def landing_page(request):
    # Hanya mengambil field yang dibutuhkan untuk menghemat RAM dan I/O database
    locations_qs = Location.objects.filter(is_active=True).values(
        'name', 'address', 'latitude', 'longitude'
    )[:100]

    locations = [
        {
            'name': loc['name'],
            'address': loc['address'],
            'latitude': float(loc['latitude']),
            'longitude': float(loc['longitude']),
        }
        for loc in locations_qs
    ]
    return render(request, 'index.html', {'locations': locations})


@require_GET
def geocode_location(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({"error": "Masukkan nama lokasi."}, status=400)

    if len(query) > 200:
        return JsonResponse({"error": "Kata kunci terlalu panjang."}, status=400)

    # 1. Cek Cache
    cache_key = "nominatim:" + query.casefold()
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return JsonResponse({"results": cached_result})

    # 2. Query Params
    params = urlencode({
        "q": query,
        "format": "jsonv2",
        "limit": 5,
        "countrycodes": "id",
        "accept-language": "id",
    })

    url = f"https://nominatim.openstreetmap.org/search?{params}"

    # 3. Header Request dengan User-Agent Valid
    # PASTI KAN mengubah email kontak ke email asli / format domain yang valid
    req = Request(
        url,
        headers={
            "User-Agent": "KelolaKitaApp/1.0 (contact: admin@kelolakita.id)",
            "Accept": "application/json",
        },
    )

    try:
        with urlopen(req, timeout=8) as response:
            results = json.loads(response.read().decode("utf-8"))

        # Simpan ke Cache selama 24 Jam
        cache.set(cache_key, results, timeout=86400)
        return JsonResponse({"results": results})

    except HTTPError as exc:
        print(f"[Geocode Error] OSM HTTP {exc.code}: {exc.reason}")
        return JsonResponse(
            {"error": "Layanan pencarian lokasi sedang sibuk. Coba lagi nanti."},
            status=503,
        )
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"[Geocode Error] Network/JSON Exception: {exc}")
        return JsonResponse(
            {"error": "Gagal terhubung ke layanan lokasi."},
            status=503,
        )
