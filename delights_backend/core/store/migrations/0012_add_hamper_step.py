from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0011_alter_hamper_price_label"),
    ]

    operations = [
        migrations.AddField(
            model_name="hamper",
            name="hamper_step",
            field=models.CharField(
                max_length=32,
                choices=[
                    ("base", "Box"),
                    ("office", "Office Essentials"),
                    ("gourmet", "Gourmet Treats"),
                    ("personalize", "Personalize"),
                ],
                blank=True,
                default="",
                help_text="Assign product to a custom hamper-builder step (for admin/frontend).",
            ),
        ),
    ]
