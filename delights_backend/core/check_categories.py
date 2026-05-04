import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from store.models import Category

print("=" * 60)
print("CURRENT CATEGORY STRUCTURE")
print("=" * 60)

parents = Category.objects.filter(parent__isnull=True).order_by('position', 'name')

for parent in parents:
    print(f"\n☐ {parent.name} (ID: {parent.id}, Position: {parent.position})")
    children = Category.objects.filter(parent=parent).order_by('position', 'name')
    for idx, child in enumerate(children):
        is_last = idx == children.count() - 1
        prefix = "↳" if is_last else "├─"
        print(f"  {prefix} {child.name} (ID: {child.id}, Position: {child.position})")

print("\n" + "=" * 60)
print(f"Total categories: {Category.objects.count()}")
print("=" * 60)
