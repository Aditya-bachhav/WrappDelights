from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from django.contrib.auth import views as auth_views
from store.views import (
    corporate_page,
    corporate_success,
    dashboard,
    dashboard_categories,
    dashboard_corporate,
    dashboard_create_category,
    dashboard_create_product,
    dashboard_create_section,
    dashboard_delete_category,
    dashboard_delete_inquiry,
    dashboard_delete_product,
    dashboard_delete_section,
    dashboard_edit_category,
    dashboard_edit_product,
    dashboard_edit_section,
    dashboard_inquiry_detail,
    dashboard_products,
    dashboard_sections,
    dashboard_toggle_product,
    home,
    product_detail,
    product_list,
    search_view,
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # Public catalog flow
    path("", home, name="home"),
    path("home/", home, name="home_alt"),
    path("products/", product_list, name="products"),
    path("products/<int:product_id>/", product_detail, name="product_detail"),
    path("corporate/", corporate_page, name="corporate"),
    path("corporate-success/", corporate_success, name="corporate_success"),
    path("search/", search_view, name="search"),

    # Dashboard — overview
    path("dashboard/", dashboard, name="dashboard"),

    # Dashboard — products
    path("dashboard/products/", dashboard_products, name="dashboard_products"),
    path("dashboard/products/create/", dashboard_create_product, name="dashboard_create_product"),
    path("dashboard/products/<int:product_id>/edit/", dashboard_edit_product, name="dashboard_edit_product"),
    path("dashboard/products/<int:product_id>/delete/", dashboard_delete_product, name="dashboard_delete_product"),
    path("dashboard/products/<int:product_id>/toggle/", dashboard_toggle_product, name="dashboard_toggle_product"),

    # Dashboard — categories
    path("dashboard/categories/", dashboard_categories, name="dashboard_categories"),
    path("dashboard/categories/create/", dashboard_create_category, name="dashboard_create_category"),
    path("dashboard/categories/<int:category_id>/edit/", dashboard_edit_category, name="dashboard_edit_category"),
    path("dashboard/categories/<int:category_id>/delete/", dashboard_delete_category, name="dashboard_delete_category"),

    # Dashboard — homepage sections
    path("dashboard/sections/", dashboard_sections, name="dashboard_sections"),
    path("dashboard/sections/create/", dashboard_create_section, name="dashboard_create_section"),
    path("dashboard/sections/<int:section_id>/edit/", dashboard_edit_section, name="dashboard_edit_section"),
    path("dashboard/sections/<int:section_id>/delete/", dashboard_delete_section, name="dashboard_delete_section"),

    # Dashboard — corporate inquiries
    path("dashboard/corporate-requests/", dashboard_corporate, name="dashboard_corporate"),
    path("dashboard/corporate-requests/<int:inquiry_id>/", dashboard_inquiry_detail, name="dashboard_inquiry_detail"),
    path("dashboard/corporate-requests/<int:inquiry_id>/delete/", dashboard_delete_inquiry, name="dashboard_delete_inquiry"),

    # Auth
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path("account/", dashboard, name="account"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
