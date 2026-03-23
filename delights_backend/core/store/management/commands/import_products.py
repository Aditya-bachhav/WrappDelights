from django.core.management.base import BaseCommand
from django.db import transaction
import csv
import os

from store.models import Category, Hamper


class Command(BaseCommand):
    help = 'Bulk import products from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file}'))
            return
        
        success_count = 0
        error_count = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Expected columns: name, category, sku, short_description, specifications, tags
            for row in reader:
                try:
                    with transaction.atomic():
                        # Get or create category
                        category_name = row.get('category', '').strip()
                        category = None
                        if category_name:
                            category, _ = Category.objects.get_or_create(
                                name=category_name,
                                defaults={'is_active': True}
                            )
                        
                        # Create product
                        product = Hamper.objects.create(
                            name=row.get('name', '').strip(),
                            category=category,
                            short_description=row.get('short_description', '').strip()[:220],
                            included_items=row.get('specifications', '').strip(),
                            is_active=True,
                        )
                        
                        success_count += 1
                        self.stdout.write(self.style.SUCCESS(f'✓ Created: {product.name} (SKU: {product.sku})'))
                        
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'✗ Error creating product: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Import complete: {success_count} products created, {error_count} errors'))
