from django.db import models
from django.db import models
import uuid
# Create your models here.
from django.db import models

class Enquiry(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    income = models.FloatField()
    city = models.CharField(max_length=100)
    property_type = models.CharField(max_length=100)
    budget = models.FloatField()
    followups = models.IntegerField()
    site_visited = models.BooleanField()
    booked = models.BooleanField()  # Target column (Interested / Not Interested)

    def __str__(self):
        return self.name


class FeatureImportance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    feature = models.CharField(max_length=200)
    importance = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(null=True, blank=True)  # e.g. mean SHAP, sign

    def __str__(self):
        return f"{self.feature} ({self.importance:.4f})"

class AIGeneratedReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    metrics = models.JSONField(null=True, blank=True)  # accuracy, f1, counts
    file_path = models.CharField(max_length=512, null=True, blank=True)  # PDF path if generated

    def __str__(self):
        return self.title
