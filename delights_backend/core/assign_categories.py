import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from store.models import Hamper, Category

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

def assign_categories():
    """Assign categories to products based on name keywords"""
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
                    print(f"✓ {hamper.name} → {category_name}")
                    updated_count += 1
                    break
                except Category.DoesNotExist:
                    print(f"✗ Category '{category_name}' not found")
                    break
        else:
            # If no keyword matched, assign to "Hamper Product"
            try:
                default_category = Category.objects.get(name='Hamper Product')
                hamper.category = default_category
                hamper.save()
                print(f"✓ {hamper.name} → Hamper Product (default)")
                updated_count += 1
            except Category.DoesNotExist:
                print(f"✗ Default category 'Hamper Product' not found")

    print(f"\n\nTotal updated: {updated_count}")

    # Show statistics
    print("\n\nCategory Distribution:")
    for cat in Category.objects.all():
        count = cat.hampers.count()
        print(f"  {cat.name}: {count} products")

if __name__ == '__main__':
    assign_categories()
