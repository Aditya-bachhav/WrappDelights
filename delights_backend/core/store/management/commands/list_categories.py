"""
Management command to list all available categories
"""
from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = 'List all available product categories'

    def handle(self, *args, **options):
        Category = apps.get_model('store', 'Category')
        
        categories = Category.objects.filter(is_active=True).select_related('parent').order_by('parent__name', 'name')
        
        self.stdout.write(self.style.SUCCESS("Available Categories:\n"))
        
        parent_categories = {}
        for cat in categories:
            if cat.parent:
                if cat.parent.slug not in parent_categories:
                    parent_categories[cat.parent.slug] = []
                parent_categories[cat.parent.slug].append(cat)
            else:
                if '__parent__' not in parent_categories:
                    parent_categories['__parent__'] = []
                parent_categories['__parent__'].append(cat)
        
        # Print parent categories first
        for cat in parent_categories.get('__parent__', []):
            self.stdout.write(f"  {cat.name} (slug: {cat.slug})")
        
        # Then print subcategories under their parents
        for parent_slug, children in parent_categories.items():
            if parent_slug != '__parent__':
                for child in children:
                    parent = Category.objects.get(slug=parent_slug)
                    self.stdout.write(f"    └─ {child.name} (slug: {child.slug})")
