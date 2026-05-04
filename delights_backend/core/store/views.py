import json
import re
import logging
import os
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import transaction
from django.db.models import Q, Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from delights_backend.core.store import models
from .models import Category, CorporateInquiry, Hamper, HamperImage, HomepageSection
from django.http import JsonResponse
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


def _files_debug_info(files):
    info = []
    for key in files.keys():
        for f in files.getlist(key):
            info.append(
                {
                    "field": key,
                    "name": getattr(f, "name", ""),
                    "size": getattr(f, "size", None),
                    "content_type": getattr(f, "content_type", ""),
                }
            )
    return info


def _media_storage_state():
    media_root = Path(settings.MEDIA_ROOT)
    parent = media_root.parent
    return {
        "media_root": str(media_root),
        "media_exists": media_root.exists(),
        "media_is_dir": media_root.is_dir() if media_root.exists() else False,
        "media_writable": os.access(media_root, os.W_OK) if media_root.exists() else False,
        "parent_exists": parent.exists(),
        "parent_writable": os.access(parent, os.W_OK) if parent.exists() else False,
    }


def _save_gallery_images(hamper, gallery_images, start_position=0):
    """Save gallery images one by one so one bad file does not abort the whole request."""
    uploaded = 0
    failed = []

    for offset, image in enumerate(gallery_images):
        try:
            HamperImage.objects.create(
                hamper=hamper,
                image=image,
                position=start_position + offset,
            )
            uploaded += 1
        except Exception as e:
            failed.append(
                {
                    "name": getattr(image, "name", "unknown"),
                    "error": str(e),
                }
            )
            logger.exception(
                "Gallery image upload failed. hamper_id=%s image_name=%s",
                hamper.id,
                getattr(image, "name", "unknown"),
            )

    return uploaded, failed


CATALOG_NAV_CATEGORIES = [
    "corporate",
    "wedding",
    "employee",
]

CATALOG_QUICK_LINKS = [
    "Diwali",
    "Wedding",
    "Corporate",
    "Employee",
]

CATEGORY_DISPLAY_NAMES = {
    "corporate": "Corporate Gifting",
    "wedding": "Wedding & Events",
    "employee": "Employees / Welcome Kit",
    "corporate-christmas-gifts": "Corporate Gifts",
    "diwali-gifts": "Diwali Gifts",
    "new-year-gifts": "New Year Gifts",
    "womens-day-gifts": "Women's Day Gifts",
    "office-welcome-kit": "Office Welcome Kit",
    "employee-welcome-kit": "Employee Welcome Kit",
    "wedding-hampers": "Wedding Hampers",
    "wedding-accessories": "Wedding Accessories",
    "wedding-return-gifts": "Wedding Return Gifts",
}

_success_whatsapp_digits = ''.join(ch for ch in getattr(settings, "WHATSAPP_NUMBER", "9309810348") if ch.isdigit())
if len(_success_whatsapp_digits) == 10:
    SUCCESS_WHATSAPP_RAW = f"91{_success_whatsapp_digits}"
else:
    SUCCESS_WHATSAPP_RAW = _success_whatsapp_digits

SESSION_KIT_KEY = "kit"
STEP_CONFIG = {
    1: {
        "slug": "base",
        "title": "Choose Box",
        "subtitle": "Pick the box or hamper base you want to build on.",
        "category_hints": ["box", "hamper", "packaging"],
    },
    2: {
        "slug": "office",
        "title": "Office Essentials",
        "subtitle": "Add the practical everyday items that define the hamper.",
        "category_hints": ["office", "essentials", "stationery", "work"],
    },
    3: {
        "slug": "gourmet",
        "title": "Gourmet Treats",
        "subtitle": "Add premium food and treat selections to elevate the kit.",
        "category_hints": ["gourmet", "treat", "snack", "food"],
    },
    4: {
        "slug": "housewarming",
        "title": "House Warming",
        "subtitle": "Finish with gifts that suit a warm home celebration.",
        "category_hints": ["house", "warming", "home", "decor"],
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
    primary_category = hamper.categories.order_by("position", "name").first() or hamper.category
    return {
        "product_id": hamper.id,
        "name": hamper.name,
        "price": price,
        "quantity": max(1, int(quantity or 1)),
        "category": primary_category.name if primary_category else "",
        "image": getattr(hamper, "cover_image_url", "") or "",
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
        Hamper.objects.filter(is_active=True)
        .filter(Q(category__is_active=True) | Q(categories__is_active=True) | Q(category__isnull=True))
        .select_related("category")
        .prefetch_related("categories")
        .order_by("name")
        .distinct()
    )
    step = STEP_CONFIG.get(step_number)
    if not step:
        return base_qs

    hints = step.get("category_hints") or []
    query = Q()
    for hint in hints:
        query |= Q(category__slug__icontains=hint)
        query |= Q(category__name__icontains=hint)
        query |= Q(categories__slug__icontains=hint)
        query |= Q(categories__name__icontains=hint)
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


def _dashboard_category_queryset():
    """Return active categories ordered for parent-first hierarchical rendering."""
    return Category.objects.filter(is_active=True).select_related("parent").order_by(
        "parent__position",
        "parent__name",
        "position",
        "name",
    )


def _normalize_posted_int_ids(values):
    """Convert posted ID values to ints, dropping invalid entries."""
    normalized = []
    for value in values:
        try:
            normalized.append(int(value))
        except (TypeError, ValueError):
            continue
    return normalized

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

def page_not_found(request, exception=None):
    """Handle 404 errors with a custom page."""
    return render(request, "404.html", status=404)

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
    best_sellers = active_hampers.filter(is_bestseller=True)[:12]

    corporate_welcome = active_hampers.filter(homepage_sections__section_type="corporate_welcome").distinct()[:12]
    event_section = active_hampers.filter(homepage_sections__section_type="event_hampers").distinct()[:12]
    festival_hampers = active_hampers.filter(homepage_sections__section_type="festival_hampers").distinct()[:12]

    section_prefetch = Prefetch(
        "hampers",
        queryset=active_hampers,
        to_attr="active_hampers",
    )
    homepage_sections = HomepageSection.objects.filter(is_active=True).prefetch_related(section_prefetch)

    categories = list(Category.objects.filter(is_active=True))
    for category in categories:
        category.display_name = CATEGORY_DISPLAY_NAMES.get(category.slug, category.name)

    # Get top-level categories (for quick navigation)
    top_level_categories = Category.objects.filter(is_active=True, parent__isnull=True).prefetch_related('children').order_by('position')

    return render(
        request,
        "home.html",
        {
            "featured_hampers": featured_hampers,
            "best_sellers": best_sellers,
            "corporate_welcome_hampers": corporate_welcome,
            "event_hampers": event_hampers if event_hampers.exists() else event_section,
            "festival_hampers": festival_hampers,
            "homepage_sections": homepage_sections,
            "categories": categories,
            "top_level_categories": top_level_categories,
            "catalog_nav_categories": CATALOG_NAV_CATEGORIES,
        },
    )


def product_list(request):
    hampers = Hamper.objects.filter(is_active=True).select_related("category").prefetch_related("categories")
    category_slug = request.GET.get("category", "").strip()
    search_query = request.GET.get("q", "").strip()
    active_category_label = CATEGORY_DISPLAY_NAMES.get(
        category_slug,
        category_slug.replace("-", " ").title() if category_slug else "",
    )

    sort = request.GET.get("sort", "").strip()

    if category_slug:
        hampers = hampers.filter(
            Q(category__slug=category_slug)
            | Q(category__name__iexact=category_slug)
            | Q(categories__slug=category_slug)
            | Q(categories__name__iexact=category_slug)
        ).distinct()
    if search_query:
        hampers = hampers.filter(
            Q(name__icontains=search_query)
            | Q(short_description__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(included_items__icontains=search_query)
            | Q(category__name__icontains=search_query)
            | Q(categories__name__icontains=search_query)
        ).distinct()

    if sort == "price":
        hampers = hampers.order_by("base_price", "id")
    elif sort == "-price":
        hampers = hampers.order_by("-base_price", "-id")
    elif sort == "newest":
        hampers = hampers.order_by("-created_at", "-id")
    else:
        hampers = hampers.order_by("id")

    categories = list(Category.objects.filter(is_active=True))
    for category in categories:
        category.display_name = CATEGORY_DISPLAY_NAMES.get(category.slug, category.name)
    return render(
        request,
        "products.html",
        {
            "products": hampers,
            "categories": categories,
            "active_category": category_slug,
            "active_category_label": active_category_label,
            "search_query": search_query,
            "catalog_nav_categories": CATALOG_NAV_CATEGORIES,
            "catalog_quick_links": CATALOG_QUICK_LINKS,
        },
    )


def product_detail(request, product_id):
    hamper = get_object_or_404(
        Hamper.objects.select_related("category").prefetch_related("images", "categories"),
        id=product_id,
        is_active=True,
    )
    hamper_categories = hamper.categories.all()
    related = (
        Hamper.objects.filter(is_active=True)
        .filter(
            Q(category=hamper.category)
            | Q(categories__in=hamper_categories)
        )
        .exclude(id=hamper.id)
        .select_related("category")
        .prefetch_related("categories")
        .distinct()[:8]
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
            "step_count": len(STEP_CONFIG),
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
            "step": {"number": len(STEP_CONFIG) + 1, "title": "Review & Submit Inquiry"},
            "step_count": len(STEP_CONFIG),
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

    hamper = Hamper.objects.filter(id=product_id, is_active=True).select_related("category").prefetch_related("categories").first()
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
            | Q(categories__name__icontains=query)
        ).select_related("category").prefetch_related("categories").distinct()

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
    products = Hamper.objects.select_related("category").prefetch_related("categories").all().order_by("-created_at")
    # Filter
    cat_filter = request.GET.get("category", "")
    status_filter = request.GET.get("status", "")
    search_q = request.GET.get("q", "").strip()
    if cat_filter:
        products = products.filter(Q(category__slug=cat_filter) | Q(categories__slug=cat_filter)).distinct()
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
        try:
            # Early validation: reject overly large uploads to avoid worker OOMs/timeouts
            max_size = getattr(settings, "MAX_UPLOAD_SIZE", 6 * 1024 * 1024)
            cover_image_preview = request.FILES.get("cover_image")
            if cover_image_preview and getattr(cover_image_preview, 'size', 0) > max_size:
                messages.error(request, f"Cover image too large (max {int(getattr(settings, 'MAX_UPLOAD_MB', 6))} MB)")
                return redirect("dashboard_create_product")
            for gi in request.FILES.getlist("gallery"):
                if getattr(gi, 'size', 0) > max_size:
                    messages.error(request, f"One of the gallery images is too large (max {int(getattr(settings, 'MAX_UPLOAD_MB', 6))} MB)")
                    return redirect("dashboard_create_product")
            selected_category_ids = request.POST.getlist("categories")
            selected_categories = list(
                Category.objects.filter(id__in=selected_category_ids, is_active=True)
            )
            # Primary category = first by position/name
            primary_category = (
                min(selected_categories, key=lambda c: (c.position, c.name))
                if selected_categories else None
            )

            # Parse base_price: the form sends a plain number, so use Decimal directly
            raw_price = request.POST.get("base_price", "").strip()
            try:
                base_price = Decimal(raw_price) if raw_price else None
            except (InvalidOperation, ValueError):
                base_price = None

            hamper = Hamper.objects.create(
                name=request.POST.get("name", "").strip(),
                category=primary_category,
                hamper_step=(request.POST.get("hamper_step") or "").strip(),
                short_description=request.POST.get("short_description", "").strip(),
                description=request.POST.get("description", "").strip(),
                included_items=request.POST.get("included_items", "").strip(),
                base_price=base_price,
                price_label=request.POST.get("price_label", "").strip(),
                min_bulk_quantity=int(request.POST.get("min_bulk_quantity") or 25),
                is_featured=request.POST.get("is_featured") == "on",
                is_event_special=request.POST.get("is_event_special") == "on",
                is_active=request.POST.get("is_active") == "on",
            )

            cover_image = request.FILES.get("cover_image")
            if cover_image:
                try:
                    hamper.cover_image = cover_image
                    hamper.save(update_fields=["cover_image"])
                except Exception:
                    logger.exception(
                        "Cover image upload failed. hamper_id=%s cover_name=%s",
                        hamper.id,
                        getattr(cover_image, "name", "unknown"),
                    )

            section_ids = request.POST.getlist("homepage_sections")
            if section_ids:
                hamper.homepage_sections.set(
                    HomepageSection.objects.filter(id__in=section_ids)
                )

            # set() triggers the m2m_changed signal which auto-adds parent categories
            if selected_categories:
                hamper.categories.set(selected_categories)

            gallery_images = request.FILES.getlist("gallery")
            _, failed_images = _save_gallery_images(hamper, gallery_images)

            if failed_images:
                failed_names = ", ".join(item["name"] for item in failed_images[:3])
                first_error = failed_images[0].get("error") or "Unknown upload error"
                messages.warning(
                    request,
                    f'Hamper "{hamper.name}" created, but {len(failed_images)} gallery image(s) failed: '
                    f'{failed_names}. Error: {first_error}',
                )
            else:
                messages.success(request, f'Hamper "{hamper.name}" created successfully.')
            return redirect("dashboard_products")

        except Exception as e:
            logger.exception(
                "Product create failed. POST keys=%s FILE keys=%s FILE details=%s MEDIA state=%s",
                list(request.POST.keys()),
                list(request.FILES.keys()),
                _files_debug_info(request.FILES),
                _media_storage_state(),
            )
            messages.error(request, f"Create failed: {type(e).__name__}: {e}")
            return redirect("dashboard_create_product")

    return render(
        request,
        "dashboard/create_product.html",
        {
            "categories": Category.objects.filter(is_active=True).select_related("parent").order_by("parent__position", "parent__name", "position", "name"),
            "homepage_sections": HomepageSection.objects.filter(is_active=True),
            "selected_category_ids": [],
            "selected_section_ids": [],
        },
    )


@login_required
@user_passes_test(admin_check)
def dashboard_edit_product(request, product_id):
    hamper = get_object_or_404(Hamper, id=product_id)

    if request.method == "POST":
        try:
            selected_category_ids = request.POST.getlist("categories")
            selected_categories = list(
                Category.objects.filter(id__in=selected_category_ids, is_active=True)
            )
            primary_category = (
                min(selected_categories, key=lambda c: (c.position, c.name))
                if selected_categories else None
            )

            # Parse base_price from plain number input
            raw_price = request.POST.get("base_price", "").strip()
            try:
                base_price = Decimal(raw_price) if raw_price else None
            except (InvalidOperation, ValueError):
                base_price = None

            hamper.name = request.POST.get("name", "").strip()
            hamper.category = primary_category
            hamper.short_description = request.POST.get("short_description", "").strip()
            hamper.description = request.POST.get("description", "").strip()
            hamper.included_items = request.POST.get("included_items", "").strip()
            hamper.base_price = base_price
            hamper.price_label = request.POST.get("price_label", "").strip()
            hamper.min_bulk_quantity = int(request.POST.get("min_bulk_quantity") or 25)
            hamper.is_featured = request.POST.get("is_featured") == "on"
            hamper.is_event_special = request.POST.get("is_event_special") == "on"
            hamper.is_active = request.POST.get("is_active") == "on"
            hamper.hamper_step = (request.POST.get("hamper_step") or "").strip()
            hamper.save()

            cover_image = request.FILES.get("cover_image")
            if cover_image:
                try:
                    hamper.cover_image = cover_image
                    hamper.save(update_fields=["cover_image"])
                except Exception:
                    logger.exception(
                        "Cover image upload failed on edit. hamper_id=%s cover_name=%s",
                        hamper.id,
                        getattr(cover_image, "name", "unknown"),
                    )

            section_ids = request.POST.getlist("homepage_sections")
            hamper.homepage_sections.set(HomepageSection.objects.filter(id__in=section_ids))

            # set() triggers m2m_changed → ensure_parent_categories auto-adds parents
            hamper.categories.set(selected_categories)

            # Handle gallery deletions
            delete_ids = request.POST.getlist("delete_gallery")
            if delete_ids:
                HamperImage.objects.filter(id__in=delete_ids, hamper=hamper).delete()

            # Add new gallery images
            gallery_images = request.FILES.getlist("gallery")
            existing_count = hamper.images.count()
            _, failed_images = _save_gallery_images(hamper, gallery_images, start_position=existing_count)

            if failed_images:
                failed_names = ", ".join(item["name"] for item in failed_images[:3])
                first_error = failed_images[0].get("error") or "Unknown upload error"
                messages.warning(
                    request,
                    f'Hamper "{hamper.name}" updated, but {len(failed_images)} gallery image(s) failed: '
                    f'{failed_names}. Error: {first_error}',
                )
            else:
                messages.success(request, f'Hamper "{hamper.name}" updated successfully.')
            return redirect("dashboard_products")

        except Exception as e:
            logger.exception(
                "Product edit failed. product_id=%s POST keys=%s FILE keys=%s FILE details=%s MEDIA state=%s",
                product_id,
                list(request.POST.keys()),
                list(request.FILES.keys()),
                _files_debug_info(request.FILES),
                _media_storage_state(),
            )
            messages.error(request, f"Update failed: {type(e).__name__}: {e}")
            return redirect("dashboard_edit_product", product_id=product_id)

    # GET — render the form with pre-selected state
    assigned_category_ids = list(hamper.categories.values_list("id", flat=True))

    return render(
        request,
        "dashboard/edit_product.html",
        {
            "hamper": hamper,
            # Pass categories ordered so parents come before their children
            "categories": Category.objects.filter(is_active=True).select_related("parent").order_by("parent__position", "parent__name", "position", "name"),
            # Plain list of ints — Django template `in` operator works correctly against this
            "assigned_category_ids": assigned_category_ids,
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


@login_required
@user_passes_test(admin_check)
def dashboard_toggle_bestseller(request, product_id):
    """Toggle the `is_bestseller` flag for a product from the dashboard."""
    hamper = get_object_or_404(Hamper, id=product_id)
    hamper.is_bestseller = not hamper.is_bestseller
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
            image = request.FILES.get("image")
            if image:
                cat.image = image
                cat.save(update_fields=["image"])
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
        image = request.FILES.get("image")
        if image:
            category.image = image
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
        # save selected categories (optional)
        selected = request.POST.getlist("categories")
        if selected:
            cats = Category.objects.filter(id__in=[int(x) for x in selected if x.isdigit()])
            section.categories.set(cats)
        messages.success(request, f'Section "{section.title}" created.')
        return redirect("dashboard_sections")
    section_choices = HomepageSection.SECTION_CHOICES
    categories = Category.objects.filter(is_active=True).order_by("position", "name")
    return render(request, "dashboard/create_section.html", {"section_choices": section_choices, "categories": categories})


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
        # update categories selection
        selected = request.POST.getlist("categories")
        if selected:
            cats = Category.objects.filter(id__in=[int(x) for x in selected if x.isdigit()])
            section.categories.set(cats)
        else:
            section.categories.clear()
        messages.success(request, f'Section "{section.title}" updated.')
        return redirect("dashboard_sections")
    section_choices = HomepageSection.SECTION_CHOICES
    categories = Category.objects.filter(is_active=True).order_by("position", "name")
    assigned_ids = list(section.categories.values_list("id", flat=True))
    return render(request, "dashboard/edit_section.html", {"section": section, "section_choices": section_choices, "categories": categories, "assigned_ids": assigned_ids})


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
