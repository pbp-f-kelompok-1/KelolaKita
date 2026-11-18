from rest_framework import serializers

from education.models import Article, Distribution, Event


class ArticleSerializer(serializers.ModelSerializer):
    cover_url = serializers.SerializerMethodField()

    def get_cover_url(self, article):
        return self.context["request"].build_absolute_uri(article.cover["src"])

    class Meta:
        model = Article
        fields = ("slug", "title", "summary", "category_label", "read_minutes", "cover_url")


class ArticleDetailSerializer(ArticleSerializer):
    class Meta(ArticleSerializer.Meta):
        fields = (*ArticleSerializer.Meta.fields, "body")


class EventSerializer(serializers.ModelSerializer):
    location_name = serializers.CharField(source="location.name")

    class Meta:
        model = Event
        fields = ("id", "title", "start_at", "location_name")


class DistributionSerializer(serializers.ModelSerializer):
    destination_name = serializers.CharField(source="destination.name")

    class Meta:
        model = Distribution
        fields = ("id", "item_name", "quantity", "distributed_at", "destination_name")
