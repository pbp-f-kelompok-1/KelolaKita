from unittest.mock import patch

from django.core.cache import cache
from django.test import SimpleTestCase
from django.urls import reverse


class GeocodingTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.addCleanup(cache.clear)
        self.url = reverse("Location:geocode_location")

    @patch("Location.views.urlopen")
    def test_success_is_cached_by_normalized_search(self, urlopen):
        urlopen.return_value.__enter__.return_value.read.return_value = (
            b'[{"lat":"-6.4","lon":"106.8","display_name":"Depok"}]'
        )
        first = self.client.get(self.url, {"q": " Depok "})
        cached = self.client.get(self.url, {"q": "DEPOK"})
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["results"][0]["display_name"], "Depok")
        self.assertEqual(cached.json(), first.json())
        urlopen.assert_called_once()

    @patch("Location.views.urlopen", side_effect=TimeoutError)
    def test_unavailable_provider_returns_controlled_response(self, urlopen):
        result = self.client.get(self.url, {"q": "Depok"})
        self.assertEqual(result.status_code, 503)
        self.assertIn("layanan lokasi", result.json()["error"])

    @patch("Location.views.urlopen")
    def test_invalid_query_does_not_reach_provider(self, urlopen):
        for query in (" ", "l" * 201):
            with self.subTest(length=len(query)):
                self.assertEqual(self.client.get(self.url, {"q": query}).status_code, 400)
        urlopen.assert_not_called()
