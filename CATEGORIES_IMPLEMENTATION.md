# Hierarchical Product Categories Implementation

## Overview
Your Wrapp Delights admin interface now supports hierarchical (nested) category selection when creating and editing products (Hampers). Products can be assigned to multiple categories, and the primary category (first selected) is automatically synced for filtering.

## How It Works

### 1. **Category Hierarchy Structure**
Categories are organized in parent-child relationships:

```
☐ Wedding (Parent)
  ├─ Wedding Return Gifts (Child)
  ├─ Wedding Accessories (Child)
  ↳ Wedding Hampers (Child)

☐ Employee (Parent)
  ├─ Employee Welcome Kit (Child)
  ↳ Office Welcome Kit (Child)

☐ Corporate (Parent)
  ├─ Corporate Christmas Gifts (Child)
  ├─ Women's Day Gifts (Child)
  ├─ New Year Gifts (Child)
  ↳ Diwali Gifts (Child)
```

**Symbols:**
- `☐` = Parent category
- `├─` = Child category (not last)
- `↳` = Last child category

### 2. **Product-Category Assignment**

When editing or creating a product in the admin:

1. Navigate to **Products → Hampers**
2. Click **Add Hamper** or edit an existing one
3. Look for the **"📂 Categories & Organization"** section
4. Select as many categories as needed using checkboxes
5. The first selected category becomes the **primary category** (used for filters)

### 3. **Key Features**

✅ **Multi-select**: Products can belong to multiple categories
✅ **Hierarchical display**: Visual tree structure with indentation
✅ **Auto-primary category**: First selected category is set as primary
✅ **Clean UI**: Easy-to-read checkbox interface with visual hierarchy
✅ **Responsive**: Works on all device sizes

---

## Setting Up Categories

If categories aren't already set up, run:

```bash
python manage.py setup_categories
```

This command creates all the parent and child categories automatically.

### Manual Category Creation

If you need to add categories manually:

1. Go to **Admin → Categories**
2. Click **Add Category**
3. Fill in the category name
4. If it's a subcategory, select the **Parent** category
5. Set the **Position** number (for ordering)
6. Upload an optional **Image**
7. Click **Save**

---

## Technical Details

### Components

**1. HierarchicalCategoryWidget** (`admin.py`)
- Custom Django form widget
- Renders categories in a tree structure
- Shows parent categories with ☐ symbol
- Shows child categories with ├─ or ↳ symbols
- Includes CSS styling for visual hierarchy

**2. HamperAdminForm** (`admin.py`)
- Custom form for the Hamper model
- Uses `HierarchicalCategoryWidget` for the `categories` field
- Automatically slugifies product names

**3. HamperAdmin** (`admin.py`)
- Admin interface for products (Hampers)
- Organizes fields into logical fieldsets:
  - Basic Information
  - **📂 Categories & Organization** (highlighted)
  - Product Details
  - Pricing
  - Display Options
- `save_related()` method syncs primary category

**4. Category Model** (`models.py`)
- `parent` field: ForeignKey to self for hierarchy
- `get_indent_display()`: Returns indented name for display
- Parent categories have `parent=None`

---

## Admin Interface Walkthrough

### Adding a New Product

1. **Go to Django Admin** → **Store → Hampers**
2. **Click "Add Hamper"**
3. **Fill in Basic Information:**
   - Product Name
   - Slug (auto-generated from name)
   - Hamper Step (Base, Office, Gourmet, Personalize)
   - Cover Image

4. **📂 Select Categories** (Important!):
   ```
   ☐ Wedding
     ├─ Wedding Return Gifts ✓ (selected)
     ├─ Wedding Accessories
     ↳ Wedding Hampers ✓ (selected)
   
   ☐ Employee
     ├─ Employee Welcome Kit
     ↳ Office Welcome Kit
   
   ☐ Corporate
     ├─ Corporate Christmas Gifts ✓ (selected)
     ├─ Women's Day Gifts
     ├─ New Year Gifts
     ↳ Diwali Gifts
   ```
   - Check all relevant categories
   - First checked category = primary category

5. **Fill in Product Details:**
   - Short Description
   - Full Description
   - Included Items (one per line)
   - Minimum Bulk Quantity

6. **Set Display Options:**
   - Is Active
   - Is Featured
   - Is Event Special
   - Is Bestseller
   - Is New Arrival
   - Homepage Sections

7. **Click "Save"**

### Result

After saving:
- Product appears in all selected categories on the frontend
- Primary category is used for admin filters
- Product can be found via search in all assigned categories
- Category relationships are maintained

---

## Database Schema

### Category Table
```
categories
├── id (PK)
├── name (CharField)
├── slug (SlugField)
├── parent_id (FK to self, nullable)
├── position (PositiveIntegerField)
├── is_active (BooleanField)
└── image (ImageField)
```

### Hamper-Category Relationship
```
hamper_categories (ManyToMany Junction Table)
├── hamper_id (FK)
├── category_id (FK)
```

---

## Filtering & Display

### Admin List View
Products can be filtered by:
- Active/Inactive status
- Featured status
- **Category** (filter by primary category)
- **Categories** (filter by any assigned category)

### Frontend Display (Context Processing)
Products are displayed in category pages based on:
1. **Primary Category** - shown in category list
2. **All Assigned Categories** - available for context data

---

## Common Tasks

### Change Product Categories
1. Go to **Admin → Store → Hampers**
2. Click on the product name
3. Scroll to **"📂 Categories & Organization"**
4. Update selections
5. Click **Save**

### View Products by Category
1. Go to **Admin → Store → Hampers**
2. Use the **"By Categories"** filter on the right
3. Select a category to see all products in it

### Create a New Category
1. Go to **Admin → Store → Categories**
2. Click **Add Category**
3. Enter name and select parent (if subcategory)
4. Click **Save**

### Manage Category Order
1. Go to **Admin → Store → Categories**
2. Use the **"Position"** column to reorder (drag or edit)
3. Click **Save**

---

## Features & Benefits

| Feature | Benefit |
|---------|---------|
| **Hierarchical Display** | Clear organization, easy to understand category structure |
| **Multi-Select** | Products can be in multiple categories without duplication |
| **Auto Primary Category** | Simplifies admin filtering and reporting |
| **Visual Indicators** | ☐, ├─, ↳ symbols make hierarchy obvious |
| **Responsive Design** | Works on desktop, tablet, mobile |
| **User-Friendly** | No technical knowledge needed |

---

## Troubleshooting

### Categories not showing?
- Make sure categories are set to `is_active = True`
- Run `python manage.py setup_categories` to create default categories

### Product not showing in category?
- Check that the category is selected in the product form
- Verify the category is `is_active = True`
- Clear any caches if using caching

### Primary category not updating?
- Ensure you select at least one category
- Save the product
- Primary category is automatically set to the first selected

---

## API Reference

### Category Model Methods
```python
# Get indented display name
category.get_indent_display()  # Returns "─ Child Name" or "Category Name"

# Get all products in this category
hampers = category.hampers.all()

# Get all child categories
children = category.children.all()

# Get parent category
parent = category.parent
```

### Hamper Model
```python
# Get all categories
categories = hamper.categories.all()

# Get primary category
primary = hamper.category

# Check if in specific category
if hamper.categories.filter(slug='wedding').exists():
    # Show in wedding section
    pass
```

---

## Notes for Developers

- Categories are ordered by `parent.position`, `parent.name`, `child.position`, `child.name`
- The widget uses CSS Grid + Flexbox for responsive layout
- Only active categories are shown in the admin
- Slugs are auto-generated from category names
- The primary category is synced in `HamperAdmin.save_related()`

---

**Last Updated:** May 3, 2026
**Status:** ✅ Implemented and Active
