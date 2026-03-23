from django.db import models
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    position = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "categories"
        ordering = ["position", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


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
    name = models.CharField(max_length=180)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hampers",
    )
    short_description = models.CharField(max_length=220, blank=True, default="")
    description = models.TextField(blank=True, default="")
    included_items = models.TextField(
        blank=True,
        default="",
        help_text="One item per line for hamper contents list",
    )
    cover_image = models.ImageField(upload_to="products/", null=True, blank=True)
    price_label = models.CharField(
        max_length=80,
        blank=True,
        default="",
        help_text="Optional display-only text like 'Starts at INR 1499'",
    )
    min_bulk_quantity = models.PositiveIntegerField(default=25)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_event_special = models.BooleanField(default=False)
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
