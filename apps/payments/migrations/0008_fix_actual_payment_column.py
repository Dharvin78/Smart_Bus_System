from django.db import migrations, models


PAYMENT_CHOICES = [
    ("Credit Card", "Credit Card"),
    ("Debit Card", "Debit Card"),
    ("Online Banking", "Online Banking"),
    ("E-Wallet", "E-Wallet"),
    ("Bank Transfer", "Bank Transfer"),
]


def make_payment_method_nullable(apps, schema_editor):
    Payment = apps.get_model("payments", "Payment")

    old_field = models.CharField(
        max_length=30,
        choices=PAYMENT_CHOICES,
        null=False,
        blank=False,
    )

    new_field = models.CharField(
        max_length=30,
        choices=PAYMENT_CHOICES,
        null=True,
        blank=True,
    )

    old_field.set_attributes_from_name("payment_method")
    new_field.set_attributes_from_name("payment_method")

    old_field.model = Payment
    new_field.model = Payment

    schema_editor.alter_field(
        Payment,
        old_field,
        new_field,
        strict=False,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0007_fix_payment_method_nullable"),
    ]

    operations = [
        migrations.RunPython(
            make_payment_method_nullable,
            reverse_code=migrations.RunPython.noop,
        ),
    ]