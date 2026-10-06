import uuid

from django.db import models


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    address = models.TextField()
    contact_person = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    open_hours = models.CharField(max_length=255)
    province = models.CharField(max_length=255)
    city = models.CharField(max_length=255)

    def __str__(self):
        return self.name