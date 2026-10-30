"""`ModelForm` untuk `Penjadwalan`, dipakai oleh `Schedule.views.show_schedule`.

Sebelum modul ini ada, `show_schedule` memvalidasi `request.POST` secara
manual field-per-field lalu memanggil `Penjadwalan.objects.create(...)`
langsung (lihat riwayat git). `PenjadwalanForm` di bawah ini menggantikan
seluruh validasi manual tersebut dengan satu `ModelForm`, supaya:

- Validasi "bentuk" tiap field (required, max_length, choices, format
  tanggal, regex nomor HP) otomatis ditangani oleh field Django biasa,
  bukan ditulis ulang satu-satu di view.
- Validasi lintas-field (`metode=kurir` wajib `alamat_penjemputan`,
  `metode=titik` wajib `lokasi_mitra`) otomatis terpanggil, karena
  `BaseModelForm._post_clean()` memanggil `instance.full_clean()`, yang
  pada gilirannya memanggil `Penjadwalan.clean()`. Sebelumnya `clean()`
  ini punya duplikat manual di view karena `.objects.create()` tidak
  memanggil `full_clean()` sama sekali.
- `.save()` menangani pembuatan instance **dan** `barang.set(...)`
  (lewat `save_m2m()`) dalam satu pemanggilan, menggantikan
  `Penjadwalan.objects.create(...)` + `.barang.set(barang_qs)` manual.

Tiga constraint yang TIDAK bisa dinyatakan lewat field model biasa tetap
perlu "disuntikkan" dari view lewat kwargs khusus di `__init__`, karena
sifatnya dinamis per-request (bukan pilihan statis seperti `choices`):

- `approved_items` — queryset `Pemeriksaan` yang boleh dipilih di field
  `barang` (barang yang sudah disetujui & belum pernah dijadwalkan).
  Tanpa ini, `ModelMultipleChoiceField` akan menerima *semua* `Pemeriksaan`
  yang ada, termasuk yang masih `menunggu` atau sudah dijadwalkan.
- `valid_dates` — kumpulan string ISO tanggal yang sedang ditawarkan di
  kalender (jendela `DATE_WINDOW_DAYS` hari ke depan). Tanpa ini, field
  `tanggal` akan menerima tanggal apa pun, termasuk tanggal lampau atau
  di luar jendela yang ditampilkan ke pengguna.
- `active_locations` — queryset `Location` yang `is_active=True`, untuk
  membatasi pilihan `lokasi_mitra` ke titik mitra yang memang sedang
  aktif.

Satu hal yang sengaja **tidak** dipindahkan ke form ini: pengecekan sisa
kuota sesi (`SESSION_QUOTAS`). Pengecekan itu perlu dijalankan ulang tepat
sebelum `.save()` di view (bukan di `form.clean()`) untuk meminimalkan
jendela race condition antara validasi dan penyimpanan saat dua pengguna
submit sesi yang sama hampir bersamaan — lihat `show_schedule` di
`views.py`.

Catatan penamaan field HTML: input radio di `schedule.html` memakai
`name="metode"`, `name="tanggal"`, dan `name="sesi"` (disamakan dengan
nama field model/form ini, bukan nama lama `method`/`date`/`session`)
supaya binding form standar Django (`field.widget.value_from_datadict`)
bisa langsung menemukan datanya di `request.POST` tanpa remapping manual.
"""

import re

from django import forms

from penanganan.models import Pemeriksaan
from Schedule.models import Penjadwalan, phone_validator


class PenjadwalanForm(forms.ModelForm):
    """Form penjadwalan penyetoran/penjemputan barang.

    Dipakai dua kali di `show_schedule`: tanpa data (GET, untuk render form
    kosong dengan nilai default) dan terikat ke `request.POST` (POST, untuk
    validasi + penyimpanan). Lihat docstring modul untuk kwargs tambahan
    yang wajib disuntikkan dari view (`approved_items`, `valid_dates`,
    `active_locations`).
    """

    barang = forms.ModelMultipleChoiceField(
        queryset=Pemeriksaan.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True,
        error_messages={
            "required": "Pilih minimal satu barang untuk dijadwalkan.",
        },
    )
    nomor_hp = forms.CharField(max_length=20)

    class Meta:
        model = Penjadwalan
        fields = [
            "barang",
            "metode",
            "tanggal",
            "sesi",
            "nama_penerima",
            "nomor_hp",
            "alamat_penjemputan",
            "alamat_latitude",
            "alamat_longitude",
            "lokasi_mitra",
            "notes",
        ]

    def __init__(self, *args, approved_items=None, valid_dates=None, active_locations=None, **kwargs):
        """Suntikkan queryset/konstrain dinamis sebelum form dipakai.

        `approved_items`/`active_locations` membatasi queryset pilihan
        valid untuk `barang`/`lokasi_mitra`; `valid_dates` (iterable string
        ISO) dipakai manual di `clean_tanggal` karena `DateField` tidak
        punya mekanisme "daftar tanggal valid" bawaan seperti `choices`
        pada `ChoiceField`.
        """
        super().__init__(*args, **kwargs)
        self.fields["barang"].queryset = (
            approved_items if approved_items is not None else Pemeriksaan.objects.none()
        )
        if active_locations is not None:
            self.fields["lokasi_mitra"].queryset = active_locations
        self._valid_dates = set(valid_dates) if valid_dates is not None else None

    def clean_tanggal(self):
        """Tolak tanggal di luar jendela kalender yang sedang ditawarkan
        (`valid_dates`), misalnya tanggal lampau atau di luar `DATE_WINDOW_DAYS`
        hari ke depan."""
        tanggal = self.cleaned_data["tanggal"]
        if self._valid_dates is not None and tanggal.isoformat() not in self._valid_dates:
            raise forms.ValidationError("Tanggal di luar rentang yang tersedia.")
        return tanggal

    def clean_nomor_hp(self):
        """Normalisasi nomor HP (buang spasi/strip) sebelum divalidasi.

        Dilakukan di `clean_nomor_hp`, bukan lewat `validators=[phone_validator]`
        langsung di field, karena validator pada field dijalankan sebelum
        hook `clean_<field>` sempat menormalisasi nilainya — nomor dengan
        strip seperti "0812-3456-789" akan ditolak duluan oleh regex
        sebelum sempat dibersihkan. Memanggil `phone_validator` secara
        manual di sini memastikan urutannya: normalisasi dulu, baru
        validasi format.
        """
        raw = self.cleaned_data.get("nomor_hp", "")
        normalized = re.sub(r"[\s-]", "", raw.strip())
        phone_validator(normalized)
        return normalized

    def clean(self):
        """Kosongkan field yang tidak relevan dengan `metode` terpilih.

        `metode=titik` tidak memakai `alamat_penjemputan`/koordinat peta,
        dan `metode=kurir` tidak memakai `lokasi_mitra`. Mengosongkannya di
        sini (sebelum `Penjadwalan.clean()` dipanggil otomatis oleh
        `_post_clean()`) mencegah data sisa dari input yang disembunyikan
        JS (misalnya alamat yang pernah diisi lalu metode diganti ke
        "titik") ikut tersimpan, dan juga memastikan validasi silang di
        `Penjadwalan.clean()` memeriksa field yang benar-benar relevan.
        """
        cleaned_data = super().clean()
        metode = cleaned_data.get("metode")
        if metode == Penjadwalan.Metode.titik:
            cleaned_data["alamat_penjemputan"] = ""
            cleaned_data["alamat_latitude"] = None
            cleaned_data["alamat_longitude"] = None
        elif metode == Penjadwalan.Metode.kurir:
            cleaned_data["lokasi_mitra"] = None
        return cleaned_data
