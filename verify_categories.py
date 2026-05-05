import django
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from store.models import Category

cats = Category.objects.all().order_by('position', 'name')
print(f"\n✓ Found {cats.count()} categories:\n")
for cat in cats:
    parent = cat.parent.name if cat.parent else "—"
    indent = "  └─ " if cat.parent else "  ► "
    print(f"{indent}{cat.name:25} ({cat.slug:25}) Parent: {parent}")
