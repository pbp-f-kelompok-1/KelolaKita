import datetime

from django.contrib import messages
from django.db.models import Count
from django.shortcuts import redirect, render

from jadwal.models import Pemeriksaan, Penjadwalan


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
    },
    {
        "value": "siang",
        "icon": "icons/sun.svg",
        "name": "Siang",
        "time": "13.00–16.30",
    },
]

SESSION_QUOTAS = {"pagi": 3, "siang": 1}

DATE_WINDOW_DAYS = 30


def _upcoming_dates(days=DATE_WINDOW_DAYS):
    today = datetime.date.today()
    dates = []
    for offset in range(days):
        day = today + datetime.timedelta(days=offset)
        dates.append({
            "iso": day.isoformat(),
            "day_abbr": DAY_ABBR_ID[day.weekday()],
            "day_num": day.day,
            "full_label": f"{DAY_FULL_ID[day.weekday()]}, {day.day} {MONTH_FULL_ID[day.month - 1]} {day.year}",
            "page": offset // 6,
        })
    return dates


def _availability_for_dates(dates):
    date_isos = [d["iso"] for d in dates]
    counts = (
        Penjadwalan.objects
        .filter(tanggal__in=date_isos)
        .values("tanggal", "sesi")
        .annotate(booked=Count("id"))
    )
    booked_map = {(row["tanggal"].isoformat(), row["sesi"]): row["booked"] for row in counts}

    availability = {}
    for d in dates:
        availability[d["iso"]] = {
            sesi: max(quota - booked_map.get((d["iso"], sesi), 0), 0)
            for sesi, quota in SESSION_QUOTAS.items()
        }
    return availability


def _approved_items():
    return Pemeriksaan.objects.exclude(kategori_penanganan="menunggu").order_by("-created_at")


def show_schedule(request):
    """Halaman penjadwalan penyetoran/penjemputan barang (modul Penyetoran & Penjemputan)."""
    dates = _upcoming_dates()
    items = _approved_items()
    today = datetime.date.today()
    current_month_label = f"{MONTH_FULL_ID[today.month - 1]} {today.year}"

    if request.method == "POST":
        method = request.POST.get("method")
        date_iso = request.POST.get("date")
        session = request.POST.get("session")
        contact = request.POST.get("contact", "").strip()
        notes = request.POST.get("notes", "").strip()
        barang_id = request.POST.get("barang")

        valid_method = any(m["value"] == method for m in PICKUP_METHODS)
        valid_date = any(d["iso"] == date_iso for d in dates)
        valid_session = session in SESSION_QUOTAS
        barang = _approved_items().filter(pk=barang_id).first() if barang_id else None

        if not (valid_method and valid_date and valid_session and contact and barang):
            messages.error(request, "Lengkapi barang, metode, tanggal, sesi, dan kontak penerima terlebih dahulu.")
            return redirect("show_schedule")

        remaining = SESSION_QUOTAS[session] - Penjadwalan.objects.filter(tanggal=date_iso, sesi=session).count()
        if remaining <= 0:
            messages.error(request, "Sesi yang dipilih sudah penuh, silakan pilih sesi lain.")
            return redirect("show_schedule")

        Penjadwalan.objects.create(
            barang=barang,
            metode=method,
            tanggal=date_iso,
            sesi=session,
            contact=contact,
            notes=notes,
        )
        messages.success(request, "Jadwal penyetoran berhasil dikonfirmasi.")
        return redirect("show_schedule")

    context = {
        "active_nav": "jadwal",
        "current_month_label": current_month_label,
        "dates": dates,
        "methods": PICKUP_METHODS,
        "sessions": PICKUP_SESSIONS,
        "items": items,
        "selected_method": PICKUP_METHODS[0]["value"],
        "selected_date": dates[0]["iso"],
        "selected_session": PICKUP_SESSIONS[0]["value"],
        "selected_item_id": items[0].pk if items else None,
        "availability": _availability_for_dates(dates),
        "contact_default": "Nabila · +62 812 3456 7890",
        "notes_default": "Hubungi saat tiba di gerbang.",
    }
    return render(request, "jadwal/schedule.html", context)
