# Generated migration to populate category hierarchy for render deployment

from django.db import migrations


def create_category_hierarchy(apps, schema_editor):
    """Create top-level and subcategories for the category hierarchy."""
    Category = apps.get_model('store', 'Category')
    
    # Avoid duplicates: check if categories already exist
    if Category.objects.filter(slug='wedding').exists():
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
    
    # Create Wedding subcategories
    Category.objects.create(
        name='Return Gifts',
        slug='return-gifts',
        parent=wedding,
        is_active=True,
        position=0
    )
    Category.objects.create(
        name='Accessories',
        slug='accessories',
        parent=wedding,
        is_active=True,
        position=1
    )
    Category.objects.create(
        name='Hampers',
        slug='hampers',
        parent=wedding,
        is_active=True,
        position=2
    )
    
    # Create Employee subcategories
    Category.objects.create(
        name='Welcome Kit',
        slug='welcome-kit',
        parent=employee,
        is_active=True,
        position=0
    )
    Category.objects.create(
        name='Office Welcome Kit',
        slug='office-welcome-kit',
        parent=employee,
        is_active=True,
        position=1
    )
    
    # Create Corporate subcategories
    Category.objects.create(
        name='Christmas Gifts',
        slug='christmas-gifts',
        parent=corporate,
        is_active=True,
        position=0
    )
    Category.objects.create(
        name='Women\'s Day Gifts',
        slug='womens-day-gifts',
        parent=corporate,
        is_active=True,
        position=1
    )
    Category.objects.create(
        name='New Year Gifts',
        slug='new-year-gifts',
        parent=corporate,
        is_active=True,
        position=2
    )
    Category.objects.create(
        name='Diwali Gifts',
        slug='diwali-gifts',
        parent=corporate,
        is_active=True,
        position=3
    )


def reverse_category_hierarchy(apps, schema_editor):
    """Delete created categories if migration is reversed."""
    Category = apps.get_model('store', 'Category')
    Category.objects.filter(slug__in=[
        'wedding', 'employee', 'corporate',
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
