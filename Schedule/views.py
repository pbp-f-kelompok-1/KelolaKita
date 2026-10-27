import datetime
import re
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from Location.models import Location
from Schedule.models import Pemeriksaan, Penjadwalan, phone_validator


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


def _approved_items():
    return (
        Pemeriksaan.objects
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


def _normalize_phone(raw):
    return re.sub(r"[\s-]", "", raw.strip())


def _safe_decimal(value):
    try:
        return Decimal(value) if value else None
    except (InvalidOperation, ValueError):
        return None


def _session_datetime(tanggal, sesi, edge="start"):
    start, end = SESSION_WINDOWS[sesi]
    clock = start if edge == "start" else end
    return timezone.make_aware(datetime.datetime.combine(tanggal, clock))


def show_schedule(request):
    """Halaman penjadwalan penyetoran/penjemputan barang (modul Penyetoran & Penjemputan)."""
    dates = _upcoming_dates()
    today = datetime.date.today()
    current_month_label = f"{MONTH_FULL_ID[today.month - 1]} {today.year}"

    selected_method = PICKUP_METHODS[0]["value"]
    selected_date = dates[0]["iso"]
    selected_session = PICKUP_SESSIONS[0]["value"]
    selected_item_ids = []
    selected_lokasi_id = ""
    nama_penerima_value = ""
    nomor_hp_value = ""
    alamat_penjemputan_value = ""
    alamat_latitude_value = ""
    alamat_longitude_value = ""
    notes_value = ""

    if request.method == "POST":
        method = request.POST.get("method", "")
        date_iso = request.POST.get("date", "")
        session = request.POST.get("session", "")
        nama_penerima = request.POST.get("nama_penerima", "").strip()
        nomor_hp = _normalize_phone(request.POST.get("nomor_hp", ""))
        alamat_penjemputan = request.POST.get("alamat_penjemputan", "").strip()
        alamat_latitude = request.POST.get("alamat_latitude", "").strip()
        alamat_longitude = request.POST.get("alamat_longitude", "").strip()
        lokasi_mitra_id = request.POST.get("lokasi_mitra", "")
        notes = request.POST.get("notes", "").strip()
        barang_ids = request.POST.getlist("barang")

        # Echo submitted values back so a validation error doesn't reset the form.
        selected_method = method or selected_method
        selected_date = date_iso or selected_date
        selected_session = session or selected_session
        selected_item_ids = barang_ids
        selected_lokasi_id = lokasi_mitra_id
        nama_penerima_value = nama_penerima
        nomor_hp_value = nomor_hp
        alamat_penjemputan_value = alamat_penjemputan
        alamat_latitude_value = alamat_latitude
        alamat_longitude_value = alamat_longitude
        notes_value = notes

        valid_method = any(m["value"] == method for m in PICKUP_METHODS)
        valid_date = any(d["iso"] == date_iso for d in dates)
        valid_session = session in SESSION_QUOTAS
        barang_qs = _approved_items().filter(pk__in=barang_ids) if barang_ids else Pemeriksaan.objects.none()
        valid_barang = bool(barang_ids) and barang_qs.count() == len(set(barang_ids))

        try:
            phone_validator(nomor_hp)
            valid_phone = True
        except ValidationError:
            valid_phone = False

        lokasi_mitra = None
        if method == "titik":
            lokasi_mitra = _active_locations().filter(pk=lokasi_mitra_id).first() if lokasi_mitra_id else None
            location_ok = lokasi_mitra is not None
        else:
            location_ok = bool(alamat_penjemputan)

        if not (valid_method and valid_date and valid_session and valid_barang
                and nama_penerima and valid_phone and location_ok):
            messages.error(
                request,
                "Lengkapi barang, metode, tanggal, sesi, nama & nomor HP penerima, "
                "serta alamat/lokasi penjemputan terlebih dahulu.",
            )
        else:
            remaining = SESSION_QUOTAS[session] - Penjadwalan.objects.filter(tanggal=date_iso, sesi=session).count()
            if remaining <= 0:
                messages.error(request, "Sesi yang dipilih sudah penuh, silakan pilih sesi lain.")
            else:
                penjadwalan = Penjadwalan.objects.create(
                    metode=method,
                    tanggal=date_iso,
                    sesi=session,
                    nama_penerima=nama_penerima,
                    nomor_hp=nomor_hp,
                    alamat_penjemputan=alamat_penjemputan if method == "kurir" else "",
                    alamat_latitude=_safe_decimal(alamat_latitude) if method == "kurir" else None,
                    alamat_longitude=_safe_decimal(alamat_longitude) if method == "kurir" else None,
                    lokasi_mitra=lokasi_mitra,
                    notes=notes,
                )
                penjadwalan.barang.set(barang_qs)
                messages.success(request, "Jadwal penyetoran berhasil dikonfirmasi.")
                return redirect("show_schedule")

    items = _approved_items()
    first_item = items.first()

    context = {
        "active_nav": "jadwal",
        "current_month_label": current_month_label,
        "dates": dates,
        "methods": PICKUP_METHODS,
        "sessions": PICKUP_SESSIONS,
        "items": items,
        "selected_method": selected_method,
        "selected_date": selected_date,
        "selected_session": selected_session,
        "selected_item_ids": selected_item_ids,
        "selected_lokasi_id": selected_lokasi_id,
        "availability": _availability_for_dates(dates),
        "contact_placeholder_name": _owner_display_name(first_item.pengguna) if first_item else "",
        "locations": _active_locations(),
        "nama_penerima_value": nama_penerima_value,
        "nomor_hp_value": nomor_hp_value,
        "alamat_penjemputan_value": alamat_penjemputan_value,
        "alamat_latitude_value": alamat_latitude_value,
        "alamat_longitude_value": alamat_longitude_value,
        "notes_value": notes_value,
    }
    return render(request, "Schedule/schedule.html", context)


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
