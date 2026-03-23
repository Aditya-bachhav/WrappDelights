import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Category, CorporateInquiry, Hamper, HamperImage, HomepageSection


CATALOG_NAV_CATEGORIES = [
    "Corporate Gifting",
    "Wedding & Events",
    "Festive Hampers",
    "Individual Products",
    "Packaging Solutions",
]


def home(request):
    active_hampers = Hamper.objects.filter(is_active=True).select_related("category")

    featured_hampers = active_hampers.filter(is_featured=True)[:12]
    event_hampers = active_hampers.filter(is_event_special=True)[:12]

    corporate_welcome = active_hampers.filter(homepage_sections__section_type="corporate_welcome").distinct()[:12]
    event_section = active_hampers.filter(homepage_sections__section_type="event_hampers").distinct()[:12]
    festival_hampers = active_hampers.filter(homepage_sections__section_type="festival_hampers").distinct()[:12]

    section_prefetch = Prefetch(
        "hampers",
        queryset=active_hampers,
        to_attr="active_hampers",
    )
    homepage_sections = HomepageSection.objects.filter(is_active=True).prefetch_related(section_prefetch)

    return render(
        request,
        "home.html",
        {
            "featured_hampers": featured_hampers,
            "corporate_welcome_hampers": corporate_welcome,
            "event_hampers": event_hampers if event_hampers.exists() else event_section,
            "festival_hampers": festival_hampers,
            "homepage_sections": homepage_sections,
            "categories": Category.objects.filter(is_active=True),
            "catalog_nav_categories": CATALOG_NAV_CATEGORIES,
        },
    )


def product_list(request):
    hampers = Hamper.objects.filter(is_active=True).select_related("category")
    category_slug = request.GET.get("category", "").strip()
    active_category_label = category_slug.replace("-", " ").title() if category_slug else ""

    if category_slug:
        hampers = hampers.filter(Q(category__slug=category_slug) | Q(category__name__iexact=category_slug))

    categories = Category.objects.filter(is_active=True)
    return render(
        request,
        "products.html",
        {
            "products": hampers,
            "categories": categories,
            "active_category": category_slug,
            "active_category_label": active_category_label,
            "catalog_nav_categories": CATALOG_NAV_CATEGORIES,
        },
    )


def product_detail(request, product_id):
    hamper = get_object_or_404(
        Hamper.objects.select_related("category").prefetch_related("images"),
        id=product_id,
        is_active=True,
    )
    related = (
        Hamper.objects.filter(is_active=True, category=hamper.category)
        .exclude(id=hamper.id)
        .select_related("category")[:8]
    )
    included_items = [
        line.strip()
        for line in re.split(r"[\n,]", hamper.included_items or "")
        if line.strip()
    ]

    if request.method == "POST":
        quantity_raw = (request.POST.get("quantity") or "").strip()
        try:
            quantity = max(1, int(quantity_raw))
        except ValueError:
            quantity = hamper.min_bulk_quantity or 1

        contact_person = (request.POST.get("contact_person") or "").strip()
        company_name = (request.POST.get("company_name") or "").strip() or "Individual Customer"
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        delivery_address = (request.POST.get("delivery_address") or "").strip()
        details = (request.POST.get("message") or "").strip()

        CorporateInquiry.objects.create(
            inquiry_type="bulk",
            hamper=hamper,
            company_name=company_name,
            contact_person=contact_person,
            email=email,
            phone=phone,
            quantity=quantity,
            delivery_address=delivery_address,
            message=details,
            customization_details=details,
        )

        return redirect(f"{reverse('product_detail', args=[hamper.id])}?inquiry=1")

    whatsapp_text = (
        f"Hi, I'm interested in SKU {hamper.id} - {hamper.name}. "
        f"MOQ={hamper.min_bulk_quantity}. Please share pricing + delivery timeline."
    )
    inquiry_submitted = request.GET.get("inquiry") == "1"

    return render(
        request,
        "product_detail.html",
        {
            "product": hamper,
            "images": hamper.images.all(),
            "related_products": related,
            "included_items": included_items,
            "whatsapp_text": whatsapp_text,
            "inquiry_submitted": inquiry_submitted,
        },
    )


def corporate_page(request):
    if request.method == "POST":
        hamper_id = request.POST.get("hamper_id")
        hamper = Hamper.objects.filter(id=hamper_id, is_active=True).first() if hamper_id else None

        CorporateInquiry.objects.create(
            inquiry_type=request.POST.get("inquiry_type", "quote"),
            hamper=hamper,
            company_name=(request.POST.get("company_name") or request.POST.get("company") or "").strip(),
            contact_person=(request.POST.get("contact_person") or request.POST.get("name") or "").strip(),
            email=request.POST.get("email", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            quantity=int(request.POST.get("quantity") or 25),
            delivery_address=(request.POST.get("delivery_address") or request.POST.get("address") or "").strip(),
            customization_details=(request.POST.get("customization_details") or request.POST.get("requirement") or "").strip(),
            message=(request.POST.get("message") or request.POST.get("requirement") or "").strip(),
        )
        return redirect("corporate_success")

    inquiry_type = request.GET.get("type", "quote")
    hamper_id = request.GET.get("hamper")
    selected_hamper = None
    if hamper_id:
        selected_hamper = Hamper.objects.filter(id=hamper_id, is_active=True).first()

    return render(
        request,
        "corporate.html",
        {
            "products": Hamper.objects.filter(is_active=True)[:12],
            "selected_hamper": selected_hamper,
            "selected_type": inquiry_type,
        },
    )


def corporate_success(request):
    return render(request, "corporate_success.html")


def search_view(request):
    query = request.GET.get("q", "").strip()
    products = Hamper.objects.none()
    if query:
        products = Hamper.objects.filter(
            Q(name__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(included_items__icontains=query)
            | Q(category__name__icontains=query)
        ).select_related("category").distinct()

    return render(
        request,
        "search.html",
        {
            "products": products,
            "query": query,
            "result_count": products.count(),
        },
    )


def admin_check(user):
    return user.is_staff


# ─── DASHBOARD ────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(admin_check)
def dashboard(request):
    context = {
        "hamper_count": Hamper.objects.count(),
        "active_hamper_count": Hamper.objects.filter(is_active=True).count(),
        "category_count": Category.objects.count(),
        "section_count": HomepageSection.objects.count(),
        "inquiry_count": CorporateInquiry.objects.count(),
        "recent_inquiries": CorporateInquiry.objects.select_related("hamper").order_by("-created_at")[:5],
        "recent_products": Hamper.objects.select_related("category").order_by("-created_at")[:5],
    }
    return render(request, "dashboard/dashboard.html", context)


# ─── PRODUCTS ─────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(admin_check)
def dashboard_products(request):
    products = Hamper.objects.select_related("category").all().order_by("-created_at")
    # Filter
    cat_filter = request.GET.get("category", "")
    status_filter = request.GET.get("status", "")
    search_q = request.GET.get("q", "").strip()
    if cat_filter:
        products = products.filter(category__slug=cat_filter)
    if status_filter == "active":
        products = products.filter(is_active=True)
    elif status_filter == "hidden":
        products = products.filter(is_active=False)
    elif status_filter == "featured":
        products = products.filter(is_featured=True)
    if search_q:
        products = products.filter(Q(name__icontains=search_q) | Q(short_description__icontains=search_q))
    return render(request, "dashboard/products.html", {
        "products": products,
        "categories": Category.objects.filter(is_active=True),
        "cat_filter": cat_filter,
        "status_filter": status_filter,
        "search_q": search_q,
    })


@login_required
@user_passes_test(admin_check)
def dashboard_create_product(request):
    if request.method == "POST":
        category = None
        category_id = request.POST.get("category")
        if category_id:
            category = Category.objects.filter(id=category_id).first()

        hamper = Hamper.objects.create(
            name=request.POST.get("name", "").strip(),
            category=category,
            short_description=request.POST.get("short_description", "").strip(),
            description=request.POST.get("description", "").strip(),
            included_items=request.POST.get("included_items", "").strip(),
            cover_image=request.FILES.get("cover_image"),
            price_label=request.POST.get("price_label", "").strip(),
            min_bulk_quantity=int(request.POST.get("min_bulk_quantity") or 25),
            is_featured=request.POST.get("is_featured") == "on",
            is_event_special=request.POST.get("is_event_special") == "on",
            is_active=request.POST.get("is_active") == "on",
        )

        section_ids = request.POST.getlist("homepage_sections")
        if section_ids:
            hamper.homepage_sections.set(HomepageSection.objects.filter(id__in=section_ids))

        gallery_images = request.FILES.getlist("gallery")
        for idx, image in enumerate(gallery_images):
            HamperImage.objects.create(hamper=hamper, image=image, position=idx)

        messages.success(request, f'Hamper "{hamper.name}" created successfully.')
        return redirect("dashboard_products")

    return render(
        request,
        "dashboard/create_product.html",
        {
            "categories": Category.objects.filter(is_active=True),
            "homepage_sections": HomepageSection.objects.filter(is_active=True),
        },
    )


@login_required
@user_passes_test(admin_check)
def dashboard_edit_product(request, product_id):
    hamper = get_object_or_404(Hamper, id=product_id)

    if request.method == "POST":
        category_id = request.POST.get("category")
        category = Category.objects.filter(id=category_id).first() if category_id else None

        hamper.name = request.POST.get("name", "").strip()
        hamper.category = category
        hamper.short_description = request.POST.get("short_description", "").strip()
        hamper.description = request.POST.get("description", "").strip()
        hamper.included_items = request.POST.get("included_items", "").strip()
        hamper.price_label = request.POST.get("price_label", "").strip()
        hamper.min_bulk_quantity = int(request.POST.get("min_bulk_quantity") or 25)
        hamper.is_featured = request.POST.get("is_featured") == "on"
        hamper.is_event_special = request.POST.get("is_event_special") == "on"
        hamper.is_active = request.POST.get("is_active") == "on"

        if request.FILES.get("cover_image"):
            hamper.cover_image = request.FILES.get("cover_image")

        hamper.save()

        section_ids = request.POST.getlist("homepage_sections")
        hamper.homepage_sections.set(HomepageSection.objects.filter(id__in=section_ids))

        # Handle gallery deletions
        delete_ids = request.POST.getlist("delete_gallery")
        if delete_ids:
            HamperImage.objects.filter(id__in=delete_ids, hamper=hamper).delete()

        # Add new gallery images
        gallery_images = request.FILES.getlist("gallery")
        existing_count = hamper.images.count()
        for idx, image in enumerate(gallery_images):
            HamperImage.objects.create(hamper=hamper, image=image, position=existing_count + idx)

        messages.success(request, f'Hamper "{hamper.name}" updated successfully.')
        return redirect("dashboard_products")

    return render(
        request,
        "dashboard/edit_product.html",
        {
            "hamper": hamper,
            "categories": Category.objects.filter(is_active=True),
            "homepage_sections": HomepageSection.objects.filter(is_active=True),
            "assigned_section_ids": list(hamper.homepage_sections.values_list("id", flat=True)),
            "gallery_images": hamper.images.all(),
        },
    )


@login_required
@user_passes_test(admin_check)
def dashboard_delete_product(request, product_id):
    hamper = get_object_or_404(Hamper, id=product_id)
    if request.method == "POST":
        name = hamper.name
        hamper.delete()
        messages.success(request, f'Hamper "{name}" deleted.')
        return redirect("dashboard_products")
    return render(request, "dashboard/confirm_delete.html", {"object": hamper, "type": "Hamper"})


@login_required
@user_passes_test(admin_check)
def dashboard_toggle_product(request, product_id):
    hamper = get_object_or_404(Hamper, id=product_id)
    hamper.is_active = not hamper.is_active
    hamper.save()
    return redirect(request.META.get("HTTP_REFERER", "dashboard_products"))


# ─── CATEGORIES ───────────────────────────────────────────────────────────────

@login_required
@user_passes_test(admin_check)
def dashboard_categories(request):
    categories = Category.objects.all().order_by("position", "name")
    return render(request, "dashboard/categories.html", {"categories": categories})


@login_required
@user_passes_test(admin_check)
def dashboard_create_category(request):
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        if name:
            cat = Category.objects.create(
                name=name,
                position=int(request.POST.get("position") or 0),
                is_active=request.POST.get("is_active") == "on",
            )
            messages.success(request, f'Category "{cat.name}" created.')
        return redirect("dashboard_categories")
    return render(request, "dashboard/create_category.html")


@login_required
@user_passes_test(admin_check)
def dashboard_edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        category.name = request.POST.get("name", "").strip()
        category.position = int(request.POST.get("position") or 0)
        category.is_active = request.POST.get("is_active") == "on"
        category.save()
        messages.success(request, f'Category "{category.name}" updated.')
        return redirect("dashboard_categories")
    return render(request, "dashboard/edit_category.html", {"category": category})


@login_required
@user_passes_test(admin_check)
def dashboard_delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if request.method == "POST":
        name = category.name
        category.delete()
        messages.success(request, f'Category "{name}" deleted.')
        return redirect("dashboard_categories")
    return render(request, "dashboard/confirm_delete.html", {"object": category, "type": "Category"})


# ─── SECTIONS ─────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(admin_check)
def dashboard_sections(request):
    return render(
        request,
        "dashboard/sections.html",
        {"sections": HomepageSection.objects.prefetch_related("hampers").all()},
    )


@login_required
@user_passes_test(admin_check)
def dashboard_create_section(request):
    if request.method == "POST":
        section = HomepageSection.objects.create(
            title=request.POST.get("title", "").strip(),
            section_type=request.POST.get("section_type", "custom"),
            subtitle=request.POST.get("subtitle", "").strip(),
            position=int(request.POST.get("position") or 0),
            is_active=request.POST.get("is_active") == "on",
        )
        messages.success(request, f'Section "{section.title}" created.')
        return redirect("dashboard_sections")
    section_choices = HomepageSection.SECTION_CHOICES
    return render(request, "dashboard/create_section.html", {"section_choices": section_choices})


@login_required
@user_passes_test(admin_check)
def dashboard_edit_section(request, section_id):
    section = get_object_or_404(HomepageSection, id=section_id)
    if request.method == "POST":
        section.title = request.POST.get("title", "").strip()
        section.section_type = request.POST.get("section_type", "custom")
        section.subtitle = request.POST.get("subtitle", "").strip()
        section.position = int(request.POST.get("position") or 0)
        section.is_active = request.POST.get("is_active") == "on"
        section.save()
        messages.success(request, f'Section "{section.title}" updated.')
        return redirect("dashboard_sections")
    section_choices = HomepageSection.SECTION_CHOICES
    return render(request, "dashboard/edit_section.html", {"section": section, "section_choices": section_choices})


@login_required
@user_passes_test(admin_check)
def dashboard_delete_section(request, section_id):
    section = get_object_or_404(HomepageSection, id=section_id)
    if request.method == "POST":
        name = section.title
        section.delete()
        messages.success(request, f'Section "{name}" deleted.')
        return redirect("dashboard_sections")
    return render(request, "dashboard/confirm_delete.html", {"object": section, "type": "Homepage Section"})


# ─── CORPORATE INQUIRIES ──────────────────────────────────────────────────────

@login_required
@user_passes_test(admin_check)
def dashboard_corporate(request):
    inquiries = CorporateInquiry.objects.select_related("hamper").all()
    type_filter = request.GET.get("type", "")
    if type_filter:
        inquiries = inquiries.filter(inquiry_type=type_filter)
    return render(
        request,
        "dashboard/corporate_requests.html",
        {
            "requests": inquiries,
            "type_filter": type_filter,
            "inquiry_choices": CorporateInquiry.INQUIRY_CHOICES,
        },
    )


@login_required
@user_passes_test(admin_check)
def dashboard_inquiry_detail(request, inquiry_id):
    inquiry = get_object_or_404(CorporateInquiry, id=inquiry_id)
    return render(request, "dashboard/inquiry_detail.html", {"inquiry": inquiry})


@login_required
@user_passes_test(admin_check)
def dashboard_delete_inquiry(request, inquiry_id):
    inquiry = get_object_or_404(CorporateInquiry, id=inquiry_id)
    if request.method == "POST":
        inquiry.delete()
        messages.success(request, "Inquiry deleted.")
        return redirect("dashboard_corporate")
    return render(request, "dashboard/confirm_delete.html", {"object": inquiry, "type": "Corporate Inquiry"})
