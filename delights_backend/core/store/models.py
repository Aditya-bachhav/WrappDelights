from django.db import models
from django.utils.text import slugify
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text='Set to create subcategory hierarchy'
    )
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to="categories/", null=True, blank=True)

    class Meta:
        db_table = "categories"
        ordering = ["position", "name"]

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    def get_indent_display(self):
        """Returns indented name for tree display"""
        depth = 0
        node = self
        while node.parent:
            depth += 1
            node = node.parent
        return "─" * (depth * 2) + " " + self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    
def ensure_parent_categories(sender, instance, action, pk_set, **kwargs):
    """When categories are added to a Hamper, also add their parent categories.

    This ensures that items assigned to a subcategory also appear under the
    parent category listings (e.g., product in "Wedding Hampers" also shows
    up under "Wedding & Events")."""
    if action != 'post_add' or not pk_set:
        return

    # Find parents of added categories
    parent_ids = set()
    for cat_id in pk_set:
        try:
            cat = Category.objects.only('id', 'parent_id').get(id=cat_id)
        except Category.DoesNotExist:
            continue
        if cat.parent_id:
            parent_ids.add(cat.parent_id)

    # Exclude those already present
    if parent_ids:
        existing_ids = set(instance.categories.values_list('id', flat=True))
        missing = parent_ids - existing_ids
        if missing:
            instance.categories.add(*missing)



class HomepageSection(models.Model):
    SECTION_CHOICES = [
        ("corporate_welcome", "Corporate Welcome Kits"),
        ("event_hampers", "Event Hampers"),
        ("festival_hampers", "Festival Hampers"),
        ("featured_hampers", "Featured Hampers"),
        ("custom", "Custom"),
    ]

    title = models.CharField(max_length=140)
    section_type = models.CharField(max_length=40, choices=SECTION_CHOICES, default="custom")
    slug = models.SlugField(max_length=160, unique=True, blank=True)
    subtitle = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    position = models.PositiveIntegerField(default=0)
    categories = models.ManyToManyField(
        "Category",
        related_name="homepage_sections",
        blank=True,
    )

    class Meta:
        db_table = "homepage_sections"
        ordering = ["position", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Hamper(models.Model):
    HAMPER_STEP_CHOICES = [
        ("base", "Box"),
        ("office", "Office Essentials"),
        ("gourmet", "Gourmet Treats"),
        ("personalize", "Personalize"),
    ]
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hampers",
    )
    categories = models.ManyToManyField(
        Category,
        related_name="multi_category_hampers",
        blank=True,
        help_text="Assign this product to one or more catalog categories.",
    )
    short_description = models.CharField(max_length=220, blank=True, default="")
    description = models.TextField(blank=True, default="")
    hamper_step = models.CharField(
        max_length=32,
        choices=HAMPER_STEP_CHOICES,
        blank=True,
        default="",
        help_text="Assign product to a custom hamper-builder step (for admin/frontend).",
    )
    included_items = models.TextField(
        blank=True,
        default="",
        help_text="One item per line for hamper contents list",
    )
    cover_image = models.ImageField(upload_to="products/", null=True, blank=True)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Numeric price used for display and totals (₹)",
    )
    price_label = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text="Optional display-only text like 'Price on request'",
    )
    min_bulk_quantity = models.PositiveIntegerField(default=25)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_event_special = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    homepage_sections = models.ManyToManyField(
        HomepageSection,
        related_name="hampers",
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "hampers"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    @property
    def sku(self):
        """Simulate a SKU based on ID if actual SKU field is missing or not migrated."""
        return f"SKU{self.pk}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

# Connect the m2m_changed handler now that `Hamper` is defined.
m2m_changed.connect(ensure_parent_categories, sender=Hamper.categories.through)


class HamperImage(models.Model):
    hamper = models.ForeignKey(Hamper, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/gallery/")
    position = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "hamper_images"
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.hamper.name} image {self.position}"


class CorporateInquiry(models.Model):
    INQUIRY_CHOICES = [
        ("quote", "Request Corporate Quote"),
        ("bulk", "Bulk Order Inquiry"),
        ("customize", "Customize for My Company"),
    ]

    inquiry_type = models.CharField(max_length=20, choices=INQUIRY_CHOICES, default="quote")
    hamper = models.ForeignKey(
        Hamper,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
    )
    company_name = models.CharField(max_length=180)
    contact_person = models.CharField(max_length=150)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=40, blank=True, default="")
    quantity = models.PositiveIntegerField(default=25)
    delivery_address = models.TextField(blank=True, default="")
    message = models.TextField(blank=True, default="")
    customization_details = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "corporate_inquiries"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company_name} - {self.contact_person}"
