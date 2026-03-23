WrappDelights – Project Specification
Overview

WrappDelights is a Django-based ecommerce platform focused on curated gift hampers and customizable hampers for individuals, events, and corporate gifting.

The platform allows customers to:

browse curated hampers

purchase ready-made hampers

build their own custom hamper by selecting products

place orders online

The platform also supports corporate bulk orders and seasonal event specials.

Core Concept

The main differentiator of WrappDelights is the Custom Hamper Builder.

Users can:

choose hamper base
add products
customize contents
checkout

This makes the store behave more like a gift assembly platform, not just a normal ecommerce store.

Access Levels

The platform has three access layers.

1. Public Pages (No Login Required)

Users can freely browse the store without creating an account.

Public pages include:

Home page
Product listing page
Product detail page
Deals sections
Event specials
Category browsing
Search results

Users can also:

Add products to cart
Add products to hamper builder

Login is not required for browsing.

2. Authenticated User Pages

Users must login to perform actions tied to identity.

Login is required for:

Checkout
Viewing orders
Saving delivery address
Saving custom hampers
Account page

Typical user flow:

browse products
↓
add to cart
↓
checkout
↓
login required

This matches the UX pattern used by Amazon.

3. Admin Authorized Pages

Admin pages are accessible only to staff users.

Admin capabilities include:

Create products
Upload product images
Manage offers
Create event specials
Mark products as featured
Manage homepage sections
View orders
View corporate requests

Admin dashboard pages include:

/dashboard
/dashboard/products
/dashboard/create-product
/dashboard/orders
/dashboard/corporate-requests
Homepage Structure

The homepage should feel like a modern ecommerce platform with dense product discovery.

Homepage sections include:

Hero banner
Today's Deals
Featured Hampers
Event Specials
Best Sellers
New Arrivals
All Products

Each section should display multiple products in horizontal scroll rows similar to Amazon.

Product Card Design

Each product card should include:

Product image
Discount badge (if offer active)
Product name
Price
Original price (strikethrough if discounted)
Add to Cart button

Cards should be compact to increase product density per screen.

Product Page

Product detail page should include:

Image gallery
Product description
Price
Discount information
Variant selection
Add to Cart
Add to Hamper
Related products
Product Variants

Products can have variants such as:

different sizes
different packaging
different contents

Each variant may have a different price.

Example:

Basic Hamper – ₹999
Premium Hamper – ₹1499
Luxury Hamper – ₹2499
Product Image Galleries

Products support multiple images.

Users can:

click thumbnails
hover preview images

similar to Amazon product galleries.

Offer System

Products can have offers.

Offer attributes:

original_price
discount_percent
discounted_price
offer_active

Example display:

₹749  ~~₹999~~
25% OFF
Location Detection

The site detects user location with browser permission.

Example banner:

Delivering to Vadodara 390001

Users can update their location manually.

Location is stored in:

session or local storage
Custom Hamper Builder

This is the core feature of WrappDelights.

Users can build their own hamper.

Flow:

Choose hamper base
Add products
Preview hamper contents
See total price
Checkout

Product pages should include a button:

Add to Hamper

This adds the item to the active custom hamper.

UI Design System

The design should be minimalist ecommerce, not luxury-heavy.

Color distribution
White: 80%
Black: 15%
Accent Yellow: 5%

Accent color:

#F5A623

Used for:

buttons
discount badges
hover states
important actions

Design principles:

clean
product-focused
minimal
high usability

Avoid:

heavy gradients
excess animations
over-designed luxury layouts
Navigation Structure

Main navigation includes:

Home
Shop
Corporate
Cart
Orders
Account
Dashboard (admin)
Product Categories

Products can belong to categories such as:

Corporate Hampers
Wedding Hampers
Festival Hampers
Luxury Hampers

Categories help users browse by occasion.

Corporate Gifting

Businesses can submit bulk gifting requests.

Corporate page allows companies to:

request quotes
specify quantity
request custom branding

Requests are visible in the admin dashboard.

Future Features

Planned upgrades include:

Payment gateway integration
Customer reviews
Inventory tracking
Shipping estimation
Recommendation engine