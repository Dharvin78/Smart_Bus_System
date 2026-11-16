from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0006_payment_payment_method"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.AlterField(
                    model_name="payment",
                    name="payment_method",
                    field=models.CharField(
                        max_length=30,
                        null=True,
                        blank=True,
                        choices=[
                            ("Credit Card", "Credit Card"),
                            ("Debit Card", "Debit Card"),
                            ("Online Banking", "Online Banking"),
                            ("E-Wallet", "E-Wallet"),
                            ("Bank Transfer", "Bank Transfer"),
                        ],
                    ),
                ),
            ],
            state_operations=[],
        ),
    ]