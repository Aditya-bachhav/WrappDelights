# Data migration to fix category slugs with correct parent prefixes

from django.db import migrations


def fix_category_slugs(apps, schema_editor):
    """Fix category slugs to include parent prefix for URL consistency."""
    Category = apps.get_model('store', 'Category')
    
    print("\n" + "="*70)
    print("HARDCODED CATEGORY SLUG FIX - Starting")
    print("="*70)
    
    # Get or create top-level categories
    wedding, _ = Category.objects.get_or_create(
        slug='wedding',
        defaults={'name': 'Wedding', 'is_active': True, 'position': 0, 'parent': None}
    )
    employee, _ = Category.objects.get_or_create(
        slug='employee',
        defaults={'name': 'Employee', 'is_active': True, 'position': 1, 'parent': None}
    )
    corporate, _ = Category.objects.get_or_create(
        slug='corporate',
        defaults={'name': 'Corporate', 'is_active': True, 'position': 2, 'parent': None}
    )
    
    # Delete old incorrect category slugs first
    old_slugs = [
        'return-gifts', 'accessories', 'hampers',
        'welcome-kit', 'office-welcome-kit',
        'christmas-gifts', 'womens-day-gifts', 'new-year-gifts', 'diwali-gifts'
    ]
    deleted_count, _ = Category.objects.filter(slug__in=old_slugs).delete()
    print(f"\n✓ Deleted {deleted_count} old categories with incorrect slugs")
    
    # Define subcategories with correct slugs
    subcategories = [
        # Wedding
        (wedding, 'Return Gifts', 'wedding-return-gifts', 0),
        (wedding, 'Accessories', 'wedding-accessories', 1),
        (wedding, 'Hampers', 'wedding-hampers', 2),
        # Employee
        (employee, 'Welcome Kit', 'employee-welcome-kit', 0),
        (employee, 'Office Welcome Kit', 'employee-office-welcome-kit', 1),
        # Corporate
        (corporate, 'Christmas Gifts', 'corporate-christmas-gifts', 0),
        (corporate, 'Women\'s Day Gifts', 'corporate-womens-day-gifts', 1),
        (corporate, 'New Year Gifts', 'corporate-new-year-gifts', 2),
        (corporate, 'Diwali Gifts', 'corporate-diwali-gifts', 3),
    ]
    
    created_count = 0
    print(f"\nCreating/updating subcategories with correct slugs:")
    for parent, name, slug, position in subcategories:
        cat, created = Category.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'parent': parent,
                'is_active': True,
                'position': position
            }
        )
        status = "✓ CREATED" if created else "✓ EXISTS"
        print(f"  {status:12} | {slug:35} | {name}")
        if created:
            created_count += 1
    
    print(f"\n✓ Created {created_count} new subcategories with correct slugs")
    print("="*70)
    print("HARDCODED CATEGORY SLUG FIX - Complete")
    print("="*70 + "\n")


def reverse_fix(apps, schema_editor):
    """Reverse: delete fixed categories."""
    pass  # Don't delete on reverse to preserve data


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0017_populate_category_hierarchy'),
    ]

    operations = [
        migrations.RunPython(fix_category_slugs, reverse_fix),
    ]
