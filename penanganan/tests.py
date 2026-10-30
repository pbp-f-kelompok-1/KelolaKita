from io import BytesIO
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import Profile
from penanganan.forms import EditPengajuanForm, PengajuanForm
from penanganan.models import FotoBarang, Pemeriksaan


class PengajuanFormTests(TestCase):
    def test_condition_radio_choices_do_not_include_blank_option(self):
        for form_class in (PengajuanForm, EditPengajuanForm):
            with self.subTest(form=form_class.__name__):
                choices = list(form_class().fields["kondisi_barang"].choices)

                self.assertEqual(choices, Pemeriksaan.PILIHAN_KONDISI)
                self.assertNotIn(("", "---------"), choices)


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

    def test_only_manager_sees_detail_review_link(self):
        list_url = reverse("penanganan:daftar_pengajuan")

        self.client.force_login(self.manager)
        manager_response = self.client.get(list_url)
        self.assertContains(manager_response, "Detail / Periksa")

        self.client.force_login(self.user)
        user_response = self.client.get(list_url)
        self.assertNotContains(user_response, "Detail / Periksa")

    def test_only_manager_role_can_review_submissions(self):
        review_url = reverse(
            "penanganan:periksa_pengajuan",
            args=[self.user_submission.pk],
        )

        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(review_url).status_code, 200)

        self.client.force_login(self.user)
        self.assertEqual(self.client.get(review_url).status_code, 403)

    def test_manager_can_delete_processed_submission(self):
        delete_url = reverse(
            "penanganan:hapus_pengajuan",
            args=[self.user_submission.pk],
        )
        self.client.force_login(self.manager)

        response = self.client.post(delete_url)

        self.assertRedirects(
            response,
            reverse("penanganan:daftar_pengajuan"),
            fetch_redirect_response=False,
        )
        self.assertFalse(
            Pemeriksaan.objects.filter(pk=self.user_submission.pk).exists()
        )

    def test_regular_user_cannot_delete_processed_submission(self):
        delete_url = reverse(
            "penanganan:hapus_pengajuan",
            args=[self.user_submission.pk],
        )
        self.client.force_login(self.user)

        response = self.client.post(delete_url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Pemeriksaan.objects.filter(pk=self.user_submission.pk).exists()
        )

    def test_manager_sees_delete_button_for_processed_submission(self):
        self.client.force_login(self.manager)

        response = self.client.get(reverse("penanganan:daftar_pengajuan"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            reverse("penanganan:hapus_pengajuan", args=[self.user_submission.pk]),
        )

    def test_regular_user_does_not_see_delete_button_for_processed_submission(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("penanganan:daftar_pengajuan"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response,
            reverse("penanganan:hapus_pengajuan", args=[self.user_submission.pk]),
        )

    def test_invalid_review_form_does_not_update_submission(self):
        self.client.force_login(self.manager)
        review_url = reverse(
            "penanganan:periksa_pengajuan",
            args=[self.user_submission.pk],
        )

        response = self.client.post(
            review_url,
            {"kategori_penanganan": "invalid", "mitra_rekomendasi": "", "rekomendasi_penanganan": ""},
        )

        self.assertEqual(response.status_code, 200)
        self.user_submission.refresh_from_db()
        self.assertEqual(self.user_submission.kategori_penanganan, "Recycle")
        self.assertTrue(response.context["form"].errors)

    def test_valid_review_form_updates_submission(self):
        self.client.force_login(self.manager)
        review_url = reverse(
            "penanganan:periksa_pengajuan",
            args=[self.user_submission.pk],
        )

        response = self.client.post(
            review_url,
            {
                "kategori_penanganan": "Reuse",
                "mitra_rekomendasi": "Mitra lokal",
                "rekomendasi_penanganan": "Dapat digunakan kembali",
            },
        )

        self.assertRedirects(
            response,
            reverse("penanganan:daftar_pengajuan"),
            fetch_redirect_response=False,
        )
        self.user_submission.refresh_from_db()
        self.assertEqual(self.user_submission.kategori_penanganan, "Reuse")
        self.assertEqual(self.user_submission.mitra_rekomendasi, "Mitra lokal")
        self.assertEqual(
            self.user_submission.rekomendasi_penanganan,
            "Dapat digunakan kembali",
        )


class EditPengajuanFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pengaju_edit")
        self.pemeriksaan = Pemeriksaan.objects.create(
            pengguna=self.user,
            nama_barang="Barang awal",
            kategori_barang="Elektronik",
            kondisi_barang="Layak pakai",
        )
        self.client.force_login(self.user)
        self.url = reverse("penanganan:edit_pengajuan", args=[self.pemeriksaan.pk])

    def test_edit_form_updates_submission_without_requiring_new_photos(self):
        response = self.client.post(
            self.url,
            {
                "nama_barang": "Barang diperbarui",
                "kategori_barang": "Pakaian",
                "kondisi_barang": "Sangat baik",
                "catatan_tambahan": "Catatan baru",
            },
        )

        self.assertRedirects(
            response,
            reverse("penanganan:daftar_pengajuan"),
            fetch_redirect_response=False,
        )
        self.pemeriksaan.refresh_from_db()
        self.assertEqual(self.pemeriksaan.nama_barang, "Barang diperbarui")
        self.assertEqual(self.pemeriksaan.kategori_barang, "Pakaian")
        self.assertEqual(self.pemeriksaan.catatan_tambahan, "Catatan baru")

    def test_invalid_edit_form_does_not_update_submission(self):
        response = self.client.post(
            self.url,
            {
                "nama_barang": "Barang diperbarui",
                "kategori_barang": "Pakaian",
                "kondisi_barang": "invalid",
                "catatan_tambahan": "Catatan baru",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.pemeriksaan.refresh_from_db()
        self.assertEqual(self.pemeriksaan.nama_barang, "Barang awal")
        self.assertIn("kondisi_barang", response.context["form"].errors)


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
    def test_submission_accepts_one_image(self):
        user = User.objects.create_user(username="pengaju_satu_foto")
        self.client.force_login(user)
        image_data = BytesIO()
        Image.new("RGB", (4, 4), color="green").save(image_data, format="PNG")

        response = self.client.post(
            reverse("penanganan:tambah_pengajuan"),
            {
                "nama_barang": "Barang uji",
                "kategori_barang": "Lainnya",
                "kondisi_barang": "Layak pakai",
                "catatan_tambahan": "",
                "foto_barang": SimpleUploadedFile(
                    "depan.png",
                    image_data.getvalue(),
                    content_type="image/png",
                ),
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("penanganan:daftar_pengajuan"))
        self.assertEqual(Pemeriksaan.objects.count(), 1)
        foto = FotoBarang.objects.get()
        self.assertTrue(foto.gambar.name.startswith("static/img/"))
        self.assertTrue(foto.gambar.storage.exists(foto.gambar.name))
        foto.gambar.delete()

    def test_submission_upload_field_uses_single_file_input(self):
        field = PengajuanForm().fields["foto_barang"]

        self.assertFalse(field.widget.allow_multiple_selected)

    def test_edit_form_does_not_require_a_new_image(self):
        self.assertFalse(EditPengajuanForm().fields["foto_barang"].required)
