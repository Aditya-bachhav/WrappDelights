from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = 'Setup hierarchical category structure'

    def handle(self, *args, **options):
        Category = apps.get_model('store', 'Category')
        # Define category hierarchy
        categories_structure = [
            {
                'name': 'Wedding',
                'slug': 'wedding',
                'position': 1,
                'children': [
                    {'name': 'Wedding Return Gifts', 'slug': 'wedding-return-gifts'},
                    {'name': 'Wedding Accessories', 'slug': 'wedding-accessories'},
                    {'name': 'Wedding Hampers', 'slug': 'wedding-hampers'},
                ]
            },
            {
                'name': 'Employee',
                'slug': 'employee',
                'position': 2,
                'children': [
                    {'name': 'Employee Welcome Kit', 'slug': 'employee-welcome-kit'},
                    {'name': 'Office Welcome Kit', 'slug': 'employee-office-welcome-kit'},
                ]
            },
            {
                'name': 'Corporate',
                'slug': 'corporate',
                'position': 3,
                'children': [
                    {'name': 'Corporate Christmas Gifts', 'slug': 'corporate-christmas-gifts'},
                    {'name': "Women's Day Gifts", 'slug': 'corporate-womens-day-gifts'},
                    {'name': 'New Year Gifts', 'slug': 'corporate-new-year-gifts'},
                    {'name': 'Diwali Gifts', 'slug': 'corporate-diwali-gifts'},
                ]
            }
        ]

        created_count = 0
        for parent_data in categories_structure:
            # Create or get parent category
            parent, created = Category.objects.get_or_create(
                slug=parent_data['slug'],
                defaults={
                    'name': parent_data['name'],
                    'position': parent_data['position'],
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created parent category: {parent.name}'))
                created_count += 1

            # Create child categories
            for idx, child_data in enumerate(parent_data.get('children', []), 1):
                child, created = Category.objects.get_or_create(
                    slug=child_data['slug'],
                    defaults={
                        'name': child_data['name'],
                        'parent': parent,
                        'position': idx,
                        'is_active': True,
                    }
                )
                if created:
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Created subcategory: {child.name}'))
                    created_count += 1

        if created_count == 0:
            self.stdout.write(self.style.WARNING('All categories already exist'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✓ Successfully created {created_count} categories'))
