import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from Location.models import Location
from Schedule.models import Pemeriksaan, Penjadwalan
from Schedule.ScheduleForm import PenjadwalanForm


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
SESSION_WINDOWS = {
    "pagi": (datetime.time(8, 0), datetime.time(11, 30)),
    "siang": (datetime.time(13, 0), datetime.time(16, 30)),
}
CANCEL_CUTOFF_HOURS = 12

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


def _approved_items(user):
    return (
        Pemeriksaan.objects
        .filter(pengguna=user)
        .exclude(kategori_penanganan="menunggu")
        .exclude(penjadwalan_set__isnull=False)
        .select_related("pengguna")
        .order_by("-created_at")
    )


def _owner_display_name(user):
    if not user:
        return ""
    return user.get_full_name() or user.username


def _active_locations():
    return Location.objects.filter(is_active=True).order_by("name")


def _session_datetime(tanggal, sesi, edge="start"):
    start, end = SESSION_WINDOWS[sesi]
    clock = start if edge == "start" else end
    return timezone.make_aware(datetime.datetime.combine(tanggal, clock))


@login_required
def show_schedule(request):
    """Halaman penjadwalan penyetoran/penjemputan barang (modul Penyetoran & Penjemputan).

    Validasi & penyimpanan dilakukan lewat `PenjadwalanForm` (lihat
    `Schedule/ScheduleForm.py`). Satu-satunya aturan bisnis yang tetap
    ditegakkan manual di sini, bukan di form, adalah re-check sisa kuota
    sesi tepat sebelum `.save()`, untuk meminimalkan race condition saat
    dua pengguna submit sesi yang sama hampir bersamaan.
    """
    dates = _upcoming_dates()
    today = datetime.date.today()
    current_month_label = f"{MONTH_FULL_ID[today.month - 1]} {today.year}"

    items = _approved_items(request.user)
    locations = _active_locations()
    form_kwargs = {
        "approved_items": items,
        "valid_dates": [d["iso"] for d in dates],
        "active_locations": locations,
    }

    if request.method == "POST":
        form = PenjadwalanForm(request.POST, **form_kwargs)
        if form.is_valid():
            tanggal = form.cleaned_data["tanggal"]
            sesi = form.cleaned_data["sesi"]
            remaining = SESSION_QUOTAS[sesi] - Penjadwalan.objects.filter(tanggal=tanggal, sesi=sesi).count()
            if remaining <= 0:
                messages.error(request, "Sesi yang dipilih sudah penuh, silakan pilih sesi lain.")
            else:
                form.save()
                messages.success(request, "Jadwal penyetoran berhasil dikonfirmasi.")
                return redirect("show_schedule")
        else:
            messages.error(
                request,
                "Lengkapi barang, metode, tanggal, sesi, nama & nomor HP penerima, "
                "serta alamat/lokasi penjemputan terlebih dahulu.",
            )
    else:
        initial = {
            "metode": PICKUP_METHODS[0]["value"],
            "tanggal": dates[0]["iso"],
            "sesi": PICKUP_SESSIONS[0]["value"],
        }
        form = PenjadwalanForm(initial=initial, **form_kwargs)

    first_item = items.first()

    context = {
        "active_nav": "jadwal",
        "current_month_label": current_month_label,
        "dates": dates,
        "methods": PICKUP_METHODS,
        "sessions": PICKUP_SESSIONS,
        "items": items,
        "selected_method": form["metode"].value() or PICKUP_METHODS[0]["value"],
        "selected_date": form["tanggal"].value() or dates[0]["iso"],
        "selected_session": form["sesi"].value() or PICKUP_SESSIONS[0]["value"],
        "selected_item_ids": form["barang"].value() or [],
        "selected_lokasi_id": form["lokasi_mitra"].value() or "",
        "availability": _availability_for_dates(dates),
        "contact_placeholder_name": _owner_display_name(first_item.pengguna) if first_item else "",
        "locations": locations,
        "nama_penerima_value": form["nama_penerima"].value() or "",
        "nomor_hp_value": form["nomor_hp"].value() or "",
        "alamat_penjemputan_value": form["alamat_penjemputan"].value() or "",
        "alamat_latitude_value": form["alamat_latitude"].value() or "",
        "alamat_longitude_value": form["alamat_longitude"].value() or "",
        "notes_value": form["notes"].value() or "",
    }
    return render(request, "Schedule/schedule.html", context)


@login_required
def schedule_list(request):
    """Riwayat jadwal penyetoran yang sudah dikonfirmasi, dengan opsi pembatalan."""
    now = timezone.now()
    bookings = (
        Penjadwalan.objects
        .prefetch_related("barang")
        .select_related("lokasi_mitra")
        .order_by("tanggal", "sesi", "-created_at")
    )

    rows = []
    for booking in bookings:
        start_dt = _session_datetime(booking.tanggal, booking.sesi, "start")
        end_dt = _session_datetime(booking.tanggal, booking.sesi, "end")
        cutoff_dt = start_dt - datetime.timedelta(hours=CANCEL_CUTOFF_HOURS)
        if now > end_dt:
            status = "selesai"
        elif now > cutoff_dt:
            status = "terkunci"
        else:
            status = "terjadwal"
        rows.append({
            "booking": booking,
            "status": status,
            "can_cancel": status == "terjadwal",
        })

    context = {
        "active_nav": "jadwal",
        "rows": rows,
    }
    return render(request, "Schedule/schedule_list.html", context)


@login_required
def cancel_schedule(request, pk):
    booking = get_object_or_404(Penjadwalan, pk=pk)
    if request.method == "POST":
        start_dt = _session_datetime(booking.tanggal, booking.sesi, "start")
        cutoff_dt = start_dt - datetime.timedelta(hours=CANCEL_CUTOFF_HOURS)
        if timezone.now() > cutoff_dt:
            messages.error(request, "Jadwal ini sudah melewati batas waktu pembatalan (12 jam sebelum sesi).")
        else:
            booking.delete()
            messages.success(request, "Jadwal berhasil dibatalkan.")
    return redirect("schedule_list")
