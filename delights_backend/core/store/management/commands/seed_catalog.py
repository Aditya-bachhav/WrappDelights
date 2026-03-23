from django.core.management.base import BaseCommand

from store.models import Category, Hamper


CATALOG_DATA = {
    "Individual Products": [
        "Desk Organizer",
        "Wooden Decor",
        "Bottles (Bamboo, Steel, Borosil)",
        "Mugs & Tumblers",
        "Keychains & Accessories",
        "Candles",
        "Religious Items",
        "Dry Fruit Containers",
    ],
    "Corporate Gifting": [
        "Employee Welcome Kits",
        "Onboarding Kits",
        "Corporate Gift Boxes",
        "Executive Hampers",
    ],
    "Wedding & Events": [
        "Wedding Welcome Boxes",
        "Return Gifts",
        "Room Hampers",
    ],
    "Festive Hampers": [
        "New Year Hampers",
        "Christmas Hampers",
        "Celebration Hampers",
    ],
    "Packaging Solutions": [
        "Magnetic Boxes",
        "Collapsible Boxes",
        "Jute Hampers",
        "Gift Baskets",
    ],
}


def default_desc(name, category):
    return (
        f"{name} crafted for {category} requirements. "
        "Ideal for premium bulk gifting with reliable fulfillment and presentation-ready quality."
    )


def default_included_items(category):
    if category in {"Corporate Gifting", "Wedding & Events", "Festive Hampers"}:
        return "Premium Assorted Items\nBranded Greeting Card\nLuxury Packaging"
    return "Customization-ready Product Unit\nGift-ready Packaging"


class Command(BaseCommand):
    help = "Seed B2B catalog categories and hamper/product entries."

    def handle(self, *args, **options):
        created_categories = 0
        created_hampers = 0
        updated_hampers = 0

        for position, (category_name, product_names) in enumerate(CATALOG_DATA.items(), start=1):
            category, category_created = Category.objects.get_or_create(
                name=category_name,
                defaults={"position": position, "is_active": True},
            )
            if not category_created:
                category.position = position
                category.is_active = True
                category.save(update_fields=["position", "is_active"])
            else:
                created_categories += 1

            for idx, product_name in enumerate(product_names):
                hamper, hamper_created = Hamper.objects.get_or_create(
                    name=product_name,
                    defaults={
                        "category": category,
                        "short_description": f"Premium {category_name.lower()} product for bulk orders.",
                        "description": default_desc(product_name, category_name),
                        "included_items": default_included_items(category_name),
                        "price_label": "Quote on request",
                        "min_bulk_quantity": 25,
                        "is_active": True,
                        "is_featured": idx < 2,
                        "is_event_special": category_name in {"Wedding & Events", "Festive Hampers"},
                    },
                )
                if hamper_created:
                    created_hampers += 1
                else:
                    hamper.category = category
                    hamper.short_description = hamper.short_description or f"Premium {category_name.lower()} product for bulk orders."
                    hamper.description = hamper.description or default_desc(product_name, category_name)
                    hamper.included_items = hamper.included_items or default_included_items(category_name)
                    hamper.price_label = hamper.price_label or "Quote on request"
                    hamper.min_bulk_quantity = hamper.min_bulk_quantity or 25
                    hamper.is_active = True
                    hamper.save()
                    updated_hampers += 1

        self.stdout.write(self.style.SUCCESS(
            f"Catalog seeded. Categories created: {created_categories}, hampers created: {created_hampers}, hampers updated: {updated_hampers}."
        ))
