"""
Management command to assign products to categories intelligently.
Tries to match product names with category keywords.
"""
from django.core.management.base import BaseCommand
from django.apps import apps


class Command(BaseCommand):
    help = 'Assign products to categories based on name matching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            type=str,
            help='Assign all products without categories to a specific category (by slug or name)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reassignment even if product already has categories'
        )

    def handle(self, *args, **options):
        Hamper = apps.get_model('store', 'Hamper')
        Category = apps.get_model('store', 'Category')
        
        assigned_count = 0
        
        # Get the target category if provided
        target_category = None
        if options.get('category'):
            try:
                target_category = Category.objects.get(
                    slug=options['category'].lower()
                ) or Category.objects.get(
                    name__iexact=options['category']
                )
                self.stdout.write(
                    self.style.SUCCESS(f"Target category: {target_category.name}")
                )
            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(
                        f"Category '{options['category']}' not found. "
                        "Use: list_categories command to see available categories."
                    )
                )
                return

        # Define keyword patterns for intelligent assignment
        category_keywords = {
            'wedding': ['wedding', 'bride', 'groom', 'marriage', 'anniversary'],
            'corporate': ['corporate', 'business', 'office', 'corporate-gifting'],
            'employee': ['employee', 'onboarding', 'new-hire', 'welcome-kit', 'starter-kit'],
            'festive': ['festive', 'diwali', 'christmas', 'new-year', 'christmas-hamper'],
            'packaging': ['box', 'hamper-box', 'packaging', 'jute'],
        }

        # Get products to process
        if target_category:
            products = Hamper.objects.filter(categories__isnull=True)
        elif options.get('force'):
            products = Hamper.objects.all()
        else:
            products = Hamper.objects.filter(categories__isnull=True)

        self.stdout.write(f"\nProcessing {products.count()} products...")
        
        for hamper in products:
            if target_category:
                # Manually assign to target category
                hamper.categories.add(target_category)
                if target_category.parent:
                    hamper.categories.add(target_category.parent)
                assigned_count += 1
                self.stdout.write(f"✓ {hamper.name} → {target_category.name}")
            else:
                # Try intelligent matching
                product_name = hamper.name.lower()
                matched_cat = None
                
                for cat_slug, keywords in category_keywords.items():
                    for keyword in keywords:
                        if keyword in product_name:
                            try:
                                matched_cat = Category.objects.get(slug=cat_slug)
                                break
                            except Category.DoesNotExist:
                                continue
                    if matched_cat:
                        break
                
                if matched_cat:
                    hamper.categories.add(matched_cat)
                    if matched_cat.parent:
                        hamper.categories.add(matched_cat.parent)
                    assigned_count += 1
                    self.stdout.write(f"✓ {hamper.name} → {matched_cat.name}")
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠ {hamper.name} - could not auto-assign")
                    )

        # Summary
        self.stdout.write(
            self.style.SUCCESS(f"\n✓ Successfully assigned {assigned_count} products")
        )
