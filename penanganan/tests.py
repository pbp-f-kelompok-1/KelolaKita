from io import BytesIO
from pathlib import Path

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import Profile
from penanganan.models import FotoBarang, Pemeriksaan
from penanganan.views import PENANGANAN_IMAGE_STORAGE


class ManagerRolePermissionTests(TestCase):
    def setUp(self):
        self.manager = User.objects.create_user(username="pengelola")
        self.manager.profile.role = Profile.Role.MANAGER
        self.manager.profile.save()
        self.user = User.objects.create_user(username="warga")

        self.user_submission = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Barang warga",
            kategori_barang="Elektronik",
            kondisi_barang="Layak pakai",
            kategori_penanganan="Recycle",
        )
        self.other_submission = Pemeriksaan.objects.create(
            pengguna=self.manager,
            nama_barang="Barang pengelola",
            kategori_barang="Elektronik",
            kondisi_barang="Layak pakai",
            kategori_penanganan="Recycle",
        )

    def test_manager_role_sees_all_submissions(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("penanganan:daftar_pengajuan"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user_submission.nama_barang)
        self.assertContains(response, self.other_submission.nama_barang)

    def test_user_role_sees_only_own_submissions(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("penanganan:daftar_pengajuan"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user_submission.nama_barang)
        self.assertNotContains(response, self.other_submission.nama_barang)

    def test_only_manager_role_can_review_submissions(self):
        review_url = reverse(
            "penanganan:periksa_pengajuan",
            args=[self.user_submission.pk],
        )

        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(review_url).status_code, 200)

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(review_url).status_code, 403)


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
