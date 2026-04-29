from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
import csv
from delights_backend.core.store import models

from .models import Category, Hamper, HamperImage, HomepageSection, CorporateInquiry


class HamperImageInline(admin.TabularInline):
    model = HamperImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("image_preview", "name", "slug", "position", "is_active")
    list_filter = ("is_active",)
    list_editable = ("position", "is_active")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}

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


def export_products_csv(modeladmin, request, queryset):
    """Export selected products to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['name', 'category', 'sku', 'short_description', 'specifications', 'tags'])
    
    for product in queryset:
        writer.writerow([
            product.name,
            product.category.name if product.category else '',
            product.sku,
            product.short_description,
            product.included_items,  # specifications field
            '',  # tags (empty for now since tags not implemented)
        ])
    
    return response
export_products_csv.short_description = "Export selected products to CSV"


@admin.register(Hamper)
class HamperAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "category",
        "min_bulk_quantity",
        "is_active",
        "is_featured",
    )
    list_filter = ("is_active", "is_featured", "category")
    list_editable = ("is_active", "is_featured")
    search_fields = ("name", "short_description", "description")
    filter_horizontal = ("homepage_sections",)
    inlines = [HamperImageInline]
    actions = [export_products_csv]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'hamper_step', 'cover_image')
        }),
        ('Product Details', {
            'fields': ('short_description', 'description', 'included_items', 'min_bulk_quantity')
        }),
        ('Display Options', {
            'fields': ('is_active', 'is_featured', 'is_event_special', 'homepage_sections')
        }),
    )
    prepopulated_fields = {"slug": ("name",)}


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
