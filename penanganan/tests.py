from io import BytesIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from penanganan.models import FotoBarang, Pemeriksaan
from penanganan.views import PENANGANAN_IMAGE_STORAGE


class DaftarPengajuanNavigationTests(TestCase):
    def test_anonymous_user_is_redirected_to_accounts_login(self):
        response = self.client.get(reverse("penanganan:daftar_pengajuan"))

        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('penanganan:daftar_pengajuan')}",
            fetch_redirect_response=False,
        )

    def test_authenticated_user_sees_penanganan_as_current_navigation(self):
        user = User.objects.create_user(username="warga")
        self.client.force_login(user)

        response = self.client.get(reverse("penanganan:daftar_pengajuan"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_nav"], "penanganan")
        self.assertContains(response, reverse("penanganan:daftar_pengajuan"))
        self.assertEqual(response.content.count(b'aria-current="page"'), 2)


class FotoBarangUploadTests(TestCase):
    def test_uploaded_images_are_saved_in_project_static_folder(self):
        user = User.objects.create_user(username="pengaju")
        self.client.force_login(user)

        uploads = []
        for name in ("depan.png", "belakang.png"):
            image_data = BytesIO()
            Image.new("RGB", (4, 4), color="green").save(image_data, format="PNG")
            uploads.append(
                SimpleUploadedFile(name, image_data.getvalue(), content_type="image/png")
            )

        response = self.client.post(
            reverse("penanganan:tambah_pengajuan"),
            {
                "nama_barang": "Barang uji",
                "kategori_barang": "Lainnya",
                "kondisi_barang": "Layak pakai",
                "catatan_tambahan": "",
                "foto_barang": uploads,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("penanganan:daftar_pengajuan"))
        self.assertEqual(Pemeriksaan.objects.count(), 1)
        foto_barang = list(FotoBarang.objects.all())
        self.assertEqual(len(foto_barang), 2)

        try:
            for foto in foto_barang:
                self.assertEqual(
                    Path(PENANGANAN_IMAGE_STORAGE.path(foto.gambar.name)).parent,
                    Path(__file__).resolve().parent.parent / "static" / "img" / "penanganan",
                )
                self.assertTrue(PENANGANAN_IMAGE_STORAGE.exists(foto.gambar.name))
        finally:
            for foto in foto_barang:
                PENANGANAN_IMAGE_STORAGE.delete(foto.gambar.name)
