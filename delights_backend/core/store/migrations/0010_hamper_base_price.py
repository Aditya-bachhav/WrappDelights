from decimal import Decimal, InvalidOperation
import re
from django.db import migrations, models


PRICE_PATTERN = re.compile(r"[0-9][0-9,]*(?:\.[0-9]+)?")


def parse_label(label: str):
    label = (label or "").strip()
    match = PRICE_PATTERN.search(label)
    if not match:
        return None
    raw = match.group(0).replace(",", "")
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def forwards(apps, schema_editor):
    Hamper = apps.get_model("store", "Hamper")
    for hamper in Hamper.objects.all():
        if hamper.base_price:
            continue
        parsed = parse_label(getattr(hamper, "price_label", ""))
        if parsed is not None:
            hamper.base_price = parsed
            hamper.save(update_fields=["base_price"])


def backwards(apps, schema_editor):
    Hamper = apps.get_model("store", "Hamper")
    Hamper.objects.update(base_price=None)


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0009_corporateinquiry_delivery_address"),
    ]

    operations = [
        migrations.AddField(
            model_name="hamper",
            name="base_price",
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                null=True,
                blank=True,
                help_text="Numeric price used for display and totals (₹)",
            ),
        ),
        migrations.RunPython(forwards, backwards),
    ]
