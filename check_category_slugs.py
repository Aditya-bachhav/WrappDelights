#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from store.models import Category

print("\nCurrent Category Slugs in Database:")
print("=" * 70)
for cat in Category.objects.all().order_by('parent_id', 'position', 'name'):
    parent_name = f"Parent: {cat.parent.name}" if cat.parent else "Top-level"
    print(f"  Slug: '{cat.slug}' | Name: '{cat.name}' | {parent_name}")

print("\n" + "=" * 70)
print("\nExpected URL paths:")
print("  /products/?category=wedding")
print("  /products/?category=wedding-return-gifts")
print("  /products/?category=wedding-accessories")
print("  /products/?category=wedding-hampers")
