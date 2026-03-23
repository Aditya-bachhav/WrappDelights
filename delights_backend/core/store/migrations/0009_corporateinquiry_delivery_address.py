from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0008_hamper_included_items_alter_corporateinquiry_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="corporateinquiry",
            name="delivery_address",
            field=models.TextField(blank=True, default=""),
        ),
    ]
