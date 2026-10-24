import datetime

from django.shortcuts import get_object_or_404, redirect, render
from main.models import Location
from main.forms import LocationForm
from django.contrib import messages


DAY_ABBR_ID = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
DAY_FULL_ID = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
MONTH_FULL_ID = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

PICKUP_METHODS = [
    {
        "value": "kurir",
        "title": "Dijemput kurir",
        "description": "Dari alamat utama",
        "summary_label": "Dijemput kurir",
        "info_title": "Estimasi kedatangan",
        "info_body": "Kurir akan menghubungi 15–30 menit sebelum tiba. Barang harap sudah dikemas.",
    },
    {
        "value": "kantor",
        "title": "Melalui kantor",
        "description": "Lobi Gedung Aruna",
        "summary_label": "Melalui kantor",
        "info_title": "Info penyerahan",
        "info_body": "Bawa barang ke lobi Gedung Aruna pada sesi yang dipilih untuk diperiksa petugas.",
    },
    {
        "value": "titik",
        "title": "Antar sendiri",
        "description": "Ke lokasi mitra",
        "summary_label": "Antar ke titik setoran",
        "info_title": "Info penyerahan",
        "info_body": "Antarkan barang ke titik setoran terdekat sesuai sesi yang dipilih.",
    },
]

PICKUP_SESSIONS = [
    {
        "value": "pagi",
        "icon": "icons/sunrise.svg",
        "name": "Pagi",
        "time": "08.00–11.30",
        "slot_count": 3,
        "badge_bg": "#e7f6ee",
        "badge_text": "#237b4b",
    },
    {
        "value": "siang",
        "icon": "icons/sun.svg",
        "name": "Siang",
        "time": "13.00–16.30",
        "slot_count": 1,
        "badge_bg": "#fff4d6",
        "badge_text": "#8a5b00",
    },
]


def _upcoming_dates(days=6):
    today = datetime.date.today()
    dates = []
    for offset in range(days):
        day = today + datetime.timedelta(days=offset)
        dates.append({
            "iso": day.isoformat(),
            "day_abbr": DAY_ABBR_ID[day.weekday()],
            "day_num": day.day,
            "full_label": f"{DAY_FULL_ID[day.weekday()]}, {day.day} {MONTH_FULL_ID[day.month - 1]} {day.year}",
        })
    return dates


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
    return render(request, "location.html", context)

def create_location(request) :
    form = LocationForm(request.POST or None)

    if request.method == "POST" and form.is_valid() :
        form.save()
        messages.success(request, "Lokasi berhasil ditambahkan")
        return redirect("show_location")

    return render(request, "location_form.html", {"name": "KelolaKita", "form": form, "active_nav": "peta"})

def delete_location(request, location_id) :
    location = get_object_or_404(Location, pk=location_id)

    if request.method == "POST" :
        location.delete()
        messages.success(request, "Lokasi berhasil dihapus!")
        return redirect("show_location")

    return redirect("show_location")

def location_detail(request, pk):
    loc = get_object_or_404(Location, pk=pk, is_active=True)
    return render(request, 'location_detail.html', {'loc': loc, 'active_nav': 'peta'})

def show_schedule(request):
    """Halaman penjadwalan penyetoran/penjemputan barang (modul Penyetoran & Penjemputan).

    Catatan: data barang yang dijadwalkan (nama barang, kategori, tujuan) masih berupa
    data contoh karena modul Pengajuan & Pemeriksaan Barang belum menyediakan model/data
    nyata untuk disambungkan. Sambungkan ke model pengajuan yang sebenarnya begitu modul
    tersebut tersedia.
    """
    dates = _upcoming_dates()
    today = datetime.date.today()
    current_month_label = f"{MONTH_FULL_ID[today.month - 1]} {today.year}"

    if request.method == "POST":
        method = request.POST.get("method")
        date_iso = request.POST.get("date")
        session = request.POST.get("session")
        contact = request.POST.get("contact", "").strip()

        valid_method = any(m["value"] == method for m in PICKUP_METHODS)
        valid_date = any(d["iso"] == date_iso for d in dates)
        valid_session = any(s["value"] == session for s in PICKUP_SESSIONS)

        if valid_method and valid_date and valid_session and contact:
            messages.success(request, "Jadwal penyetoran berhasil dikonfirmasi.")
        else:
            messages.error(request, "Lengkapi metode, tanggal, sesi, dan kontak penerima terlebih dahulu.")
        return redirect("show_schedule")

    context = {
        "active_nav": "jadwal",
        "current_month_label": current_month_label,
        "dates": dates,
        "methods": PICKUP_METHODS,
        "sessions": PICKUP_SESSIONS,
        "selected_method": PICKUP_METHODS[0]["value"],
        "selected_date": dates[0]["iso"],
        "selected_session": PICKUP_SESSIONS[0]["value"],
        "booking_item": {
            "name": "Meja belajar kayu",
            "category": "Reuse",
            "quantity_label": "1 barang",
            "destination": "Komunitas Ruang Tumbuh",
            "estimated_points": 180,
            "image": "img/schedule/item-placeholder.jpg",
        },
        "contact_default": "Nabila · +62 812 3456 7890",
        "notes_default": "Hubungi saat tiba di gerbang.",
    }
    return render(request, "schedule.html", context)