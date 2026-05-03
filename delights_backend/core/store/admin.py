from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from django import forms
import csv
from delights_backend.core.store import models

from .models import Category, Hamper, HamperImage, HomepageSection, CorporateInquiry


class HierarchicalCategoryWidget(forms.CheckboxSelectMultiple):
    """Custom widget to display categories in hierarchical tree structure"""
    
    template_name = 'admin/widgets/hierarchical_categories.html'
    
    def get_context(self, name, value, attrs):
        """Get context for the template renderer"""
        context = super().get_context(name, value, attrs)
        
        if value is None:
            value = []
        
        # Convert value to list of string IDs
        value_ids = {str(v) for v in value}
        
        # Get all active categories
        categories = Category.objects.filter(is_active=True).select_related('parent').order_by('parent__position', 'parent__name', 'position', 'name')
        
        # Build hierarchy
        parent_categories = []
        child_categories = {}
        
        for cat in categories:
            if cat.parent:
                if cat.parent.id not in child_categories:
                    child_categories[cat.parent.id] = []
                child_categories[cat.parent.id].append(cat)
            else:
                parent_categories.append(cat)
        
        # Build options structure
        options = []
        for parent in parent_categories:
            parent_option = {
                'id': parent.id,
                'name': parent.name,
                'checked': str(parent.id) in value_ids,
                'is_parent': True,
            }
            options.append(parent_option)
            
            # Add children
            children = child_categories.get(parent.id, [])
            for idx, child in enumerate(children):
                is_last = idx == len(children) - 1
                prefix = '↳' if is_last else '├─'
                child_option = {
                    'id': child.id,
                    'name': child.name,
                    'checked': str(child.id) in value_ids,
                    'is_parent': False,
                    'prefix': prefix,
                }
                options.append(child_option)
        
        context['widget']['options'] = options
        context['widget']['name'] = name
        
        return context
    
    def render(self, name, value, attrs=None, renderer=None):
        """Render categories as a hierarchical tree"""
        if value is None:
            value = []
        
        # Convert value to list of string IDs
        value_ids = {str(v) for v in value}
        
        # Get all active categories
        categories = Category.objects.filter(is_active=True).select_related('parent').order_by('parent__position', 'parent__name', 'position', 'name')
        
        # Build hierarchy
        parent_categories = []
        child_categories = {}
        
        for cat in categories:
            if cat.parent:
                if cat.parent.id not in child_categories:
                    child_categories[cat.parent.id] = []
                child_categories[cat.parent.id].append(cat)
            else:
                parent_categories.append(cat)
        
        # Build HTML
        html_parts = [
            '<div class="hierarchical-categories-widget">',
            '<style>',
            '.hierarchical-categories-widget { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }',
            '.hierarchical-categories-widget label { display: block; margin: 6px 0; cursor: pointer; user-select: none; }',
            '.hierarchical-categories-widget .cat-parent { margin-bottom: 12px; margin-left: 0; font-weight: 500; }',
            '.hierarchical-categories-widget .cat-child { margin-left: 28px; margin-top: 4px; font-size: 14px; }',
            '.hierarchical-categories-widget input[type="checkbox"] { margin-right: 8px; vertical-align: middle; cursor: pointer; }',
            '.hierarchical-categories-widget input[type="checkbox"]:hover { transform: scale(1.1); }',
            '.hierarchical-categories-widget .cat-prefix { font-family: monospace; margin-right: 4px; color: #666; }',
            '</style>',
        ]
        
        for parent in parent_categories:
            parent_checked = 'checked' if str(parent.id) in value_ids else ''
            html_parts.append(f'<label class="cat-parent">')
            html_parts.append(f'<input type="checkbox" name="{name}" value="{parent.id}" {parent_checked} />')
            html_parts.append(f'☐ {parent.name}</label>')
            
            # Add children
            children = child_categories.get(parent.id, [])
            for idx, child in enumerate(children):
                is_last = idx == len(children) - 1
                prefix = '↳' if is_last else '├─'
                child_checked = 'checked' if str(child.id) in value_ids else ''
                html_parts.append(f'<label class="cat-child">')
                html_parts.append(f'<input type="checkbox" name="{name}" value="{child.id}" {child_checked} />')
                html_parts.append(f'<span class="cat-prefix">{prefix}</span> {child.name}</label>')
        
        html_parts.append('</div>')
        
        return format_html(''.join(html_parts))


class HamperImageInline(admin.TabularInline):
    model = HamperImage
    extra = 1


class HamperAdminForm(forms.ModelForm):
    class Meta:
        model = Hamper
        fields = "__all__"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make the slug field read-only in edit mode
        if self.instance.pk:
            self.fields['slug'].widget.attrs['readonly'] = True


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("image_preview", "get_category_display", "parent_name", "slug", "position", "is_active")
    list_filter = ("is_active", "parent")
    list_editable = ("position", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'parent', 'image')
        }),
        ('Settings', {
            'fields': ('position', 'is_active')
        }),
    )

    def get_category_display(self, obj):
        """Display category with hierarchy"""
        return format_html(
            '<span style="margin-left: {}px;">{}</span>',
            (0 if not obj.parent else 20),
            obj.get_indent_display()
        )
    get_category_display.short_description = "Category"
    
    def parent_name(self, obj):
        """Show parent category"""
        return obj.parent.name if obj.parent else "—"
    parent_name.short_description = "Parent"

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:36px;height:36px;border-radius:999px;object-fit:cover;border:1px solid #ddd" />',
                obj.image.url,
            )
        return "—"

    image_preview.short_description = "Image"


@admin.register(HomepageSection)
class HomepageSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "section_type", "position", "is_active")
    list_filter = ("section_type", "is_active")
    list_editable = ("position", "is_active")
    search_fields = ("title", "subtitle")
    filter_horizontal = ("categories",)


def export_products_csv(modeladmin, request, queryset):
    """Export selected products to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['name', 'category', 'sku', 'short_description', 'specifications', 'tags'])
    
    for product in queryset:
        category_names = ", ".join(product.categories.values_list("name", flat=True))
        writer.writerow([
            product.name,
            category_names or (product.category.name if product.category else ''),
            product.sku,
            product.short_description,
            product.included_items,  # specifications field
            '',  # tags (empty for now since tags not implemented)
        ])
    
    return response
export_products_csv.short_description = "Export selected products to CSV"


@admin.register(Hamper)
class HamperAdmin(admin.ModelAdmin):
    form = HamperAdminForm
    list_display = (
        "name",
        "sku",
        "category",
        "min_bulk_quantity",
        "is_active",
        "is_featured",
        "is_bestseller",
        "is_new",
    )
    list_filter = ("is_active", "is_featured", "category", "categories")
    list_editable = ("is_active", "is_featured", "is_bestseller", "is_new")
    search_fields = ("name", "short_description", "description")
    filter_horizontal = ("categories", "homepage_sections")
    inlines = [HamperImageInline]
    actions = [export_products_csv]
    
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'hamper_step', 'cover_image')
        }),
        ('📂 Categories & Organization', {
            'fields': ('categories',),
            'description': 'Use the filter box to assign this product to one or more categories. Products will appear in the catalog under selected categories.',
            'classes': ('wide',)
        }),
        ('Product Details', {
            'fields': ('short_description', 'description', 'included_items', 'min_bulk_quantity')
        }),
        ('Pricing', {
            'fields': ('base_price', 'price_label'),
            'classes': ('collapse',)
        }),
        ('Display Options', {
            'fields': ('is_active', 'is_featured', 'is_event_special', 'is_bestseller', 'is_new', 'homepage_sections')
        }),
    )
    prepopulated_fields = {"slug": ("name",)}

    def save_related(self, request, form, formsets, change):
        """Save M2M relationships and ensure parent categories are included."""
        super().save_related(request, form, formsets, change)
        hamper = form.instance
        
        # Get all currently selected categories
        selected = list(hamper.categories.all())
        expanded_ids = {c.id for c in selected}
        
        # Automatically add parent categories so products in subcategories
        # also appear in parent category listings
        for c in selected:
            if c.parent_id:
                expanded_ids.add(c.parent_id)

        # Update with complete set (selected + parents)
        if expanded_ids:
            hamper.categories.set(sorted(expanded_ids))

        # Update the legacy single category field with the first selected category
        # This maintains backward compatibility
        primary_category = hamper.categories.order_by("position", "name").first()
        if hamper.category_id != (primary_category.id if primary_category else None):
            hamper.category = primary_category
            hamper.save(update_fields=["category"])


@admin.register(CorporateInquiry)
class CorporateInquiryAdmin(admin.ModelAdmin):
    list_display = (
        "created_at",
        "inquiry_type",
        "company_name",
        "contact_person",
        "email",
        "phone",
        "quantity",
        "hamper",
    )
    list_filter = ("inquiry_type", "created_at")
    search_fields = ("company_name", "contact_person", "email", "phone", "delivery_address", "message")
    readonly_fields = ("created_at",)


admin.site.register(HamperImage)
