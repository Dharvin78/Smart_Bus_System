from django.db import models


class SystemSetting(models.Model):

    company_name = models.CharField(
        max_length=200,
        default="Smart Bus Management System"
    )

    company_logo = models.ImageField(
        upload_to="company/",
        blank=True,
        null=True
    )

    company_email = models.EmailField(
        blank=True
    )

    company_phone = models.CharField(
        max_length=30,
        blank=True
    )

    company_address = models.TextField(
        blank=True
    )

    currency = models.CharField(
        max_length=10,
        default="RM"
    )

    timezone = models.CharField(
        max_length=100,
        default="Asia/Kuala_Lumpur"
    )

    language = models.CharField(
        max_length=50,
        default="English"
    )

    ai_enabled = models.BooleanField(
        default=True
    )

    minimum_training_records = models.PositiveIntegerField(
        default=10
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.company_name