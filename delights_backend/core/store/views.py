import json
import re
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from delights_backend.core.store import models
from .models import Category, CorporateInquiry, Hamper, HamperImage, HomepageSection
from django.contrib.auth.models import User
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST

CATALOG_NAV_CATEGORIES = [
    "Corporate Gifting",
    "Wedding & Events",
    "Festive Hampers",
    "Individual Products",
    "Packaging Solutions",
]

_success_whatsapp_digits = ''.join(ch for ch in getattr(settings, "WHATSAPP_NUMBER", "9309810348") if ch.isdigit())
if len(_success_whatsapp_digits) == 10:
    SUCCESS_WHATSAPP_RAW = f"91{_success_whatsapp_digits}"
else:
    SUCCESS_WHATSAPP_RAW = _success_whatsapp_digits

SESSION_KIT_KEY = "kit"
STEP_CONFIG = {
    1: {
        "slug": "base",
        "title": "Select Base",
        "subtitle": "Pick the box or hamper base you want to build on.",
        "category_hints": ["box", "hamper", "packaging"],
    },
    2: {
        "slug": "core",
        "title": "Select Core Products",
        "subtitle": "Add the primary products that define your hamper.",
        "category_hints": ["individual", "core", "snack", "gifting"],
    },
    3: {
        "slug": "addons",
        "title": "Select Add-ons",
        "subtitle": "Add extras and accessories to elevate the kit.",
        "category_hints": ["add", "extra", "accessory"],
    },
    4: {
        "slug": "branding",
        "title": "Branding & Customization",
        "subtitle": "Choose branding, custom cards, and finishing touches.",
        "category_hints": ["branding", "custom", "stationery"],
    },
    5: {
        "slug": "greeting",
        "title": "Greeting Card",
        "subtitle": "Personalize with a custom greeting message.",
        "category_hints": [],
    },
}


PRICE_PATTERN = re.compile(r"[0-9][0-9,]*(?:\.[0-9]+)?")


def _get_session_kit(request):
    return request.session.get(SESSION_KIT_KEY, [])


def _save_session_kit(request, kit):
    request.session[SESSION_KIT_KEY] = kit
    request.session.modified = True


def _clear_session_kit(request):
    if SESSION_KIT_KEY in request.session:
        del request.session[SESSION_KIT_KEY]
        request.session.modified = True


def _serialize_hamper_for_kit(hamper, quantity=1, step_slug=""):
    raw_price = getattr(hamper, "base_price", None)
    price = float(raw_price or 0)
    return {
        "product_id": hamper.id,
        "name": hamper.name,
        "price": price,
        "quantity": max(1, int(quantity or 1)),
        "category": hamper.category.name if hamper.category else "",
        "image": hamper.cover_image.url if hamper.cover_image else "",
        "step": step_slug,
    }


def _kit_totals(kit):
    total_price = 0
    total_quantity = 0
    for item in kit:
        qty = int(item.get("quantity") or 0)
        total_quantity += qty
        total_price += (float(item.get("price") or 0) * qty)
    return {
        "total_price": round(total_price, 2),
        "total_quantity": total_quantity,
        "item_count": len(kit),
    }


def _kit_response(kit, status=200):
    payload = {"items": kit}
    payload.update(_kit_totals(kit))
    return JsonResponse(payload, status=status)


def _get_step_config(step_number):
    step = STEP_CONFIG.get(step_number)
    if not step:
        return None

    prev_step = step_number - 1 if step_number > 1 else None
    next_step = step_number + 1 if step_number < 5 else None
    last_step_number = max(STEP_CONFIG.keys())

    return {
        **step,
        "number": step_number,
        "prev_url": reverse("custom_hamper_step", args=[prev_step]) if prev_step else None,
        "next_url": reverse("custom_hamper_step", args=[next_step]) if next_step else reverse("custom_hamper_review_alias"),
        "is_last_step": step_number == last_step_number,
    }


def _get_catalog_for_step(step_number):
    base_qs = (
        Hamper.objects.filter(is_active=True, category__is_active=True)
        .select_related("category")
        .order_by("name")
    )
    step = STEP_CONFIG.get(step_number)
    if not step:
        return base_qs

    hints = step.get("category_hints") or []
    query = Q()
    for hint in hints:
        query |= Q(category__slug__icontains=hint)
        query |= Q(category__name__icontains=hint)
        query |= Q(name__icontains=hint)

    filtered = base_qs.filter(query).distinct() if hints else base_qs
    if hints and filtered.exists():
        return filtered
    return base_qs


def _json_body(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}


def _parse_price(raw):
    """Extract a numeric price (Decimal) from user input like '₹ 1,380'."""
    match = PRICE_PATTERN.search(raw or "")
    if not match:
        return None
    cleaned = match.group(0).replace(",", "")
    try:
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None

def health(request):
    """Health check endpoint."""
    try:
        Hamper.objects.count()
        return JsonResponse({
            "status": "healthy",
            "service": "wrapp-delights",
            "version": "1.0.0"
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "status": "unhealthy",
            "service": "wrapp-delights",
            "error": str(e)
        }, status=503)

def create_admin(request):
    bootstrap_username = getattr(settings, "ADMIN_BOOTSTRAP_USERNAME", "Admin")
    bootstrap_password = getattr(settings, "ADMIN_BOOTSTRAP_PASSWORD", "D^L!G#t$0@dm/7404")
    bootstrap_email = getattr(settings, "ADMIN_BOOTSTRAP_EMAIL", "admin@example.com")

    user = User.objects.filter(username__iexact=bootstrap_username).first()
    if not user:
        user = User(username=bootstrap_username)

    user.username = bootstrap_username
    user.email = bootstrap_email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(bootstrap_password)
    user.save()
    return HttpResponse(f"Admin credentials ensured for '{bootstrap_username}'")

def _selected_products_from_inquiry(inquiry):
    combined = "\n".join(
        [
            (inquiry.customization_details or "").strip(),
            (inquiry.message or "").strip(),
        ]
    )

    items = []
    for raw_line in combined.splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            item_name = line[2:].strip()
            if item_name and item_name.lower() != "no items selected":
                items.append(item_name)

    # Keep order while removing duplicates.
    return list(dict.fromkeys(items))


def _build_whatsapp_message_from_inquiry(inquiry):
    selected_items = _selected_products_from_inquiry(inquiry)

    lines = [
        "Hi Wrapp Delights, I just submitted an inquiry on your website.",
        f"Inquiry Ref: WD-{inquiry.id}",
        f"Inquiry Type: {inquiry.get_inquiry_type_display()}",
    ]

    if inquiry.hamper:
        lines.append(f"Product: {inquiry.hamper.name}")
    if inquiry.quantity:
        lines.append(f"Quantity: {inquiry.quantity}")
    if selected_items:
        lines.append(f"Selected Items: {', '.join(selected_items)}")
    if inquiry.company_name:
        lines.append(f"Company: {inquiry.company_name}")
    if inquiry.contact_person:
        lines.append(f"Name: {inquiry.contact_person}")

    lines.append("Please confirm receipt and share next steps.")
    return "\n".join(lines)


def corporate(request):
    selected_hamper = None
    hamper_id_raw = (request.GET.get("hamper") or request.POST.get("hamper_id") or "").strip()
    if hamper_id_raw.isdigit():
        selected_hamper = Hamper.objects.filter(id=int(hamper_id_raw), is_active=True).first()

    selected_type = (request.GET.get("type") or request.POST.get("inquiry_type") or "quote").strip().lower()
    if selected_type not in {"quote", "bulk", "customize", "product"}:
        selected_type = "quote"

    if request.method == "POST":
        inquiry_type = selected_type
        if inquiry_type == "product":
            inquiry_type = "bulk"

        contact_person = (
            (request.POST.get("contact_person") or request.POST.get("name") or "").strip()
            or "Website Visitor"
        )
        company_name = (
            (request.POST.get("company_name") or request.POST.get("company") or "").strip()
            or "Individual Customer"
        )
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()

        quantity_raw = (request.POST.get("quantity") or "").strip()
        try:
            quantity = max(1, int(quantity_raw))
        except (TypeError, ValueError):
            quantity = 1

        delivery_address = (
            (request.POST.get("delivery_address") or request.POST.get("location") or "").strip()
        )
        message = (
            (request.POST.get("message") or request.POST.get("notes") or "").strip()
        )
        customization_details = (
            (request.POST.get("customization_details") or request.POST.get("requirement") or "").strip()
        )

        inquiry = CorporateInquiry.objects.create(
            inquiry_type=inquiry_type,
            hamper=selected_hamper,
            company_name=company_name,
            contact_person=contact_person,
            email=email,
            phone=phone,
            quantity=quantity,
            delivery_address=delivery_address,
            message=message,
            customization_details=customization_details,
        )

        return redirect(f"{reverse('corporate_success')}?inquiry={inquiry.id}")

    return render(
        request,
        "corporate.html",
        {
            "selected_hamper": selected_hamper,
            "selected_type": selected_type,
            "products": Hamper.objects.filter(is_active=True).order_by("-created_at")[:8],
            "whatsapp_number": SUCCESS_WHATSAPP_RAW,
            "phone_number": getattr(settings, "PHONE_NUMBER", "+91 93098 10348"),
            "phone_number_raw": getattr(settings, "PHONE_NUMBER_RAW", "+919309810348"),
        },
    )


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

    sort = request.GET.get("sort", "").strip()

    if category_slug:
        hampers = hampers.filter(Q(category__slug=category_slug) | Q(category__name__iexact=category_slug))

    if sort == "price":
        hampers = hampers.order_by("base_price", "id")
    elif sort == "-price":
        hampers = hampers.order_by("-base_price", "-id")
    elif sort == "newest":
        hampers = hampers.order_by("-created_at", "-id")
    else:
        hampers = hampers.order_by("id")

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


def corporate_success(request):
    inquiry_id = (request.GET.get("inquiry") or "").strip()
    inquiry = None

    if inquiry_id.isdigit():
        inquiry = CorporateInquiry.objects.filter(id=int(inquiry_id)).select_related("hamper").first()

    if inquiry:
        whatsapp_text = _build_whatsapp_message_from_inquiry(inquiry)
    else:
        whatsapp_text = "Hi Wrapp Delights, I just submitted an inquiry on your website. Please confirm receipt."

    return render(
        request,
        "corporate_success.html",
        {
            "inquiry": inquiry,
            "success_whatsapp_raw": SUCCESS_WHATSAPP_RAW,
            "success_whatsapp_text": whatsapp_text,
        },
    )


def custom_hamper_step(request, step_number):
    if step_number not in STEP_CONFIG:
        # If user reaches the review step number via the generic matcher, send them to review
        if step_number == 5:
            return redirect(reverse("custom_hamper_review"))
        return redirect(reverse("custom_hamper_step", args=[1]))

    step = _get_step_config(step_number)
    catalog = _get_catalog_for_step(step_number)
    kit = _get_session_kit(request)

    return render(
        request,
        "custom_hamper_step.html",
        {
            "step": step,
            "catalog": catalog,
            "kit": kit,
            "totals": _kit_totals(kit),
            "step_count": 5,
            "step_numbers": sorted(STEP_CONFIG.keys()),
        },
    )


def custom_hamper_review(request):
    kit = _get_session_kit(request)
    totals = _kit_totals(kit)

    if request.method == "POST":
        if not kit:
            messages.error(request, "Add at least one item before submitting an inquiry.")
            return redirect(reverse("custom_hamper_step", args=[1]))

        contact_person = (
            (request.POST.get("name") or request.POST.get("contact_person") or "").strip()
            or "Website Visitor"
        )
        company_name = (
            (request.POST.get("company") or request.POST.get("company_name") or "").strip()
            or "Individual Customer"
        )
        email = (request.POST.get("email") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        notes = (request.POST.get("notes") or request.POST.get("message") or "").strip()
        quantity_raw = (request.POST.get("quantity") or totals.get("total_quantity") or 1)

        try:
            quantity = max(1, int(quantity_raw))
        except ValueError:
            quantity = max(1, totals.get("total_quantity") or 1)

        item_lines = "\n".join(
            f"- {item.get('name')} x {item.get('quantity')} (₹{item.get('price')})" for item in kit
        ) or "- No items selected"

        message = (
            "Custom hamper builder inquiry.\n\n"
            f"Items:\n{item_lines}\n\n"
            f"Total Quantity: {totals.get('total_quantity')}\n"
            f"Estimated Total: ₹{totals.get('total_price')}\n\n"
            f"Notes: {notes or 'N/A'}"
        )

        inquiry = CorporateInquiry.objects.create(
            inquiry_type="customize",
            company_name=company_name,
            contact_person=contact_person,
            email=email,
            phone=phone,
            quantity=quantity,
            message=message,
            customization_details=message,
        )

        _clear_session_kit(request)
        return redirect(f"{reverse('corporate_success')}?inquiry={inquiry.id}")

    return render(
        request,
        "custom_hamper_review.html",
        {
            "kit": kit,
            "totals": totals,
            "step": {"number": 5, "title": "Review & Submit Inquiry"},
            "step_count": 5,
        },
    )


@require_POST
def custom_hamper_add_item(request):
    data = _json_body(request)
    product_id = data.get("product_id")
    step_slug = (data.get("step") or "").strip()
    quantity_raw = data.get("quantity") or 1

    try:
        product_id = int(product_id)
        quantity = max(1, int(quantity_raw))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid payload."}, status=400)

    hamper = Hamper.objects.filter(id=product_id, is_active=True).select_related("category").first()
    if not hamper:
        return JsonResponse({"error": "Product not found."}, status=404)

    kit = _get_session_kit(request)
    for item in kit:
        if item.get("product_id") == hamper.id:
            item["quantity"] = int(item.get("quantity") or 1) + quantity
            break
    else:
        kit.append(_serialize_hamper_for_kit(hamper, quantity, step_slug))

    _save_session_kit(request, kit)
    return _kit_response(kit)


@require_POST
def custom_hamper_remove_item(request):
    data = _json_body(request)
    product_id = data.get("product_id")
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid product id."}, status=400)

    kit = [item for item in _get_session_kit(request) if item.get("product_id") != product_id]
    _save_session_kit(request, kit)
    return _kit_response(kit)


@require_POST
def custom_hamper_update_quantity(request):
    data = _json_body(request)
    try:
        product_id = int(data.get("product_id"))
        quantity = int(data.get("quantity"))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid payload."}, status=400)

    kit = _get_session_kit(request)
    updated = False

    if quantity < 1:
        kit = [item for item in kit if item.get("product_id") != product_id]
        updated = True
    else:
        for item in kit:
            if item.get("product_id") == product_id:
                item["quantity"] = quantity
                updated = True
                break

    if updated:
        _save_session_kit(request, kit)
    return _kit_response(kit)


def custom_hamper_summary(request):
    kit = _get_session_kit(request)
    return _kit_response(kit)


@require_POST
def custom_hamper_clear(request):
    _clear_session_kit(request)
    return _kit_response([])


def custom_hamper_builder(request):
    return redirect(reverse("custom_hamper_step", args=[1]))


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
    return user.is_superuser


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
            base_price=_parse_price(request.POST.get("base_price")),
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
        hamper.base_price = _parse_price(request.POST.get("base_price"))
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

    inquiries = list(inquiries)
    for inquiry in inquiries:
        selected_products = _selected_products_from_inquiry(inquiry)
        inquiry.selected_products = selected_products
        inquiry.selected_products_count = len(selected_products)

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
    selected_products = _selected_products_from_inquiry(inquiry)
    return render(
        request,
        "dashboard/inquiry_detail.html",
        {
            "inquiry": inquiry,
            "selected_products": selected_products,
        },
    )


@login_required
@user_passes_test(admin_check)
def dashboard_delete_inquiry(request, inquiry_id):
    inquiry = get_object_or_404(CorporateInquiry, id=inquiry_id)
    if request.method == "POST":
        inquiry.delete()
        messages.success(request, "Inquiry deleted.")
        return redirect("dashboard_corporate")
    return render(request, "dashboard/confirm_delete.html", {"object": inquiry, "type": "Corporate Inquiry"})
