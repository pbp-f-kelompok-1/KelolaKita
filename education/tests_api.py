from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from education.models import Distribution
from education.tests import make_article, make_event, make_location


class EducationAPITests(TestCase):
    base = "/api/education/"

    def test_public_articles_and_details_exclude_unpublished_content(self):
        article = make_article()
        draft = make_article(title="Draf", is_published=False)
        future = make_article(title="Terjadwal", published_at=timezone.now() + timedelta(days=1))
        response = self.client.get(self.base + "articles/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Access-Control-Allow-Origin"], "*")
        self.assertEqual([row["slug"] for row in response.json()["results"]], [article.slug])
        self.assertEqual(
            self.client.get(f"{self.base}articles/{article.slug}/").json()["body"],
            article.body,
        )
        for hidden in (draft, future):
            self.assertEqual(self.client.get(f"{self.base}articles/{hidden.slug}/").status_code, 404)
        self.assertEqual(self.client.post(self.base + "articles/").status_code, 405)

    def test_public_agenda_and_distribution_filters(self):
        location = make_location()
        event = make_event(location)
        make_event(location, is_published=False)
        make_event(location, start_at=timezone.now() - timedelta(days=1))
        self.assertEqual(
            [row["id"] for row in self.client.get(self.base + "events/").json()["results"]],
            [event.pk],
        )
        delivered = Distribution.objects.create(
            item_name="Buku", destination=location, status=Distribution.Status.delivered,
            distributed_at=timezone.localdate() - timedelta(days=1),
        )
        Distribution.objects.create(item_name="Tas", destination=location)
        self.assertEqual(
            [row["id"] for row in self.client.get(self.base + "distributions/").json()["results"]],
            [delivered.pk],
        )
