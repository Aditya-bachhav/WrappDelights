# Generated migration to populate category hierarchy for render deployment

from django.db import migrations


def create_category_hierarchy(apps, schema_editor):
    """Create top-level and subcategories for the category hierarchy."""
    Category = apps.get_model('store', 'Category')
    
    # Clean up old categories with incorrect slugs (from previous migration attempts)
    old_slugs = ['return-gifts', 'accessories', 'hampers', 'welcome-kit', 'office-welcome-kit',
                 'christmas-gifts', 'womens-day-gifts', 'new-year-gifts', 'diwali-gifts']
    Category.objects.filter(slug__in=old_slugs).delete()
    
    # Check if categories already exist (with correct new slugs)
    if Category.objects.filter(slug='wedding').exists():
        # Categories exist, but verify subcategory slugs are correct
        existing_subcats = set(Category.objects.filter(
            slug__in=['wedding-return-gifts', 'wedding-accessories', 'wedding-hampers']
        ).values_list('slug', flat=True))
        if len(existing_subcats) == 3:
            # All correct categories already exist
            return
    
    # Create top-level categories
    wedding = Category.objects.create(
        name='Wedding',
        slug='wedding',
        position=0,
        is_active=True
    )
    
    employee = Category.objects.create(
        name='Employee',
        slug='employee',
        position=1,
        is_active=True
    )
    
    corporate = Category.objects.create(
        name='Corporate',
        slug='corporate',
        position=2,
        is_active=True
    )
    
    # Create Wedding subcategories (with parent prefix for URL consistency)
    Category.objects.create(
        name='Return Gifts',
        slug='wedding-return-gifts',
        parent=wedding,
        is_active=True,
        position=0
    )
    Category.objects.create(
        name='Accessories',
        slug='wedding-accessories',
        parent=wedding,
        is_active=True,
        position=1
    )
    Category.objects.create(
        name='Hampers',
        slug='wedding-hampers',
        parent=wedding,
        is_active=True,
        position=2
    )
    
    # Create Employee subcategories (with parent prefix for URL consistency)
    Category.objects.create(
        name='Welcome Kit',
        slug='employee-welcome-kit',
        parent=employee,
        is_active=True,
        position=0
    )
    Category.objects.create(
        name='Office Welcome Kit',
        slug='employee-office-welcome-kit',
        parent=employee,
        is_active=True,
        position=1
    )
    
    # Create Corporate subcategories (with parent prefix for URL consistency)
    Category.objects.create(
        name='Christmas Gifts',
        slug='corporate-christmas-gifts',
        parent=corporate,
        is_active=True,
        position=0
    )
    Category.objects.create(
        name='Women\'s Day Gifts',
        slug='corporate-womens-day-gifts',
        parent=corporate,
        is_active=True,
        position=1
    )
    Category.objects.create(
        name='New Year Gifts',
        slug='corporate-new-year-gifts',
        parent=corporate,
        is_active=True,
        position=2
    )
    Category.objects.create(
        name='Diwali Gifts',
        slug='corporate-diwali-gifts',
        parent=corporate,
        is_active=True,
        position=3
    )


def reverse_category_hierarchy(apps, schema_editor):
    """Delete created categories if migration is reversed."""
    Category = apps.get_model('store', 'Category')
    # Delete both old incorrect slugs and new correct slugs
    Category.objects.filter(slug__in=[
        'wedding', 'employee', 'corporate',
        # New correct slug format
        'wedding-return-gifts', 'wedding-accessories', 'wedding-hampers',
        'employee-welcome-kit', 'employee-office-welcome-kit',
        'corporate-christmas-gifts', 'corporate-womens-day-gifts', 'corporate-new-year-gifts', 'corporate-diwali-gifts',
        # Old incorrect slug format (for cleanup)
        'return-gifts', 'accessories', 'hampers',
        'welcome-kit', 'office-welcome-kit',
        'christmas-gifts', 'womens-day-gifts', 'new-year-gifts', 'diwali-gifts'
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0016_category_parent'),
    ]

    operations = [
        migrations.RunPython(create_category_hierarchy, reverse_category_hierarchy),
    ]
