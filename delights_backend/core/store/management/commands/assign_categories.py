from django.core.management.base import BaseCommand
from store.models import Hamper, Category


class Command(BaseCommand):
    help = 'Assign categories to products based on keywords in their names'

    def handle(self, *args, **options):
        # Mapping: keyword -> category name
        CATEGORY_KEYWORDS = {
            'hamper': 'Hamper Product',
            'corporate': 'Corporate Gifting',
            'wedding': 'Wedding & Events',
            'festive': 'Festive Hampers',
            'luxury': 'Individual Products',
            'box': 'Individual Products',
            'packaging': 'Packaging Solutions',
            'wrap': 'Packaging Solutions',
        }

        updated_count = 0

        for hamper in Hamper.objects.all():
            # Skip if already has a category
            if hamper.category:
                continue

            product_name = hamper.name.lower()

            # Find matching category
            for keyword, category_name in CATEGORY_KEYWORDS.items():
                if keyword in product_name:
                    try:
                        category = Category.objects.get(name=category_name)
                        hamper.category = category
                        hamper.save()
                        self.stdout.write(f"✓ {hamper.name} → {category_name}")
                        updated_count += 1
                        break
                    except Category.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f"✗ Category '{category_name}' not found"))
                        break
            else:
                # If no keyword matched, assign to "Hamper Product"
                try:
                    default_category = Category.objects.get(name='Hamper Product')
                    hamper.category = default_category
                    hamper.save()
                    self.stdout.write(f"✓ {hamper.name} → Hamper Product (default)")
                    updated_count += 1
                except Category.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"✗ Default category 'Hamper Product' not found"))

        self.stdout.write(self.style.SUCCESS(f"\n\nTotal updated: {updated_count}"))

        # Show statistics
        self.stdout.write("\n\nCategory Distribution:")
        for cat in Category.objects.all():
            count = cat.hampers.count()
            self.stdout.write(f"  {cat.name}: {count} products")
