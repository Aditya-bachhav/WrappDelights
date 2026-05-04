# Quick Start Guide - Hierarchical Categories

## Setup (One-Time)

```bash
cd delights_backend/core
python manage.py setup_categories
```

This creates all your categories automatically.

---

## Adding a Product with Categories

### Step 1: Open Admin
- Go to `http://localhost:8000/admin/`
- Navigate to **Store → Hampers**
- Click **"+ Add Hamper"**

### Step 2: Basic Info
```
Product Name:        [Your Product Name]
Slug:               [Auto-filled]
Hamper Step:        [Choose: Base, Office, Gourmet, Personalize]
Cover Image:        [Upload image]
```

### Step 3: Select Categories 📂
You'll see a hierarchical tree like this:

```
☐ Wedding
  ├─ [ ] Wedding Return Gifts
  ├─ [ ] Wedding Accessories
  ↳ [✓] Wedding Hampers

☐ Employee
  ├─ [ ] Employee Welcome Kit
  ↳ [ ] Office Welcome Kit

☐ Corporate
  ├─ [✓] Corporate Christmas Gifts
  ├─ [ ] Women's Day Gifts
  ├─ [ ] New Year Gifts
  ↳ [ ] Diwali Gifts
```

**Check all categories this product belongs to!**
✓ First checked = Primary category (for filtering)

### Step 4: Product Details
```
Short Description:   [One-liner description]
Description:         [Full details]
Included Items:      [One item per line]
Min Bulk Quantity:   [Minimum order]
```

### Step 5: Pricing (Optional)
```
Base Price:         [₹ Price]
Price Label:        [E.g., "Price on request"]
```

### Step 6: Display Options
```
Is Active:          [✓] Check this
Is Featured:        [ ] For homepage hero
Is Event Special:   [ ] For special events
Is Bestseller:      [ ] Mark as popular
Is New:             [ ] Mark as new arrival
Homepage Sections:  [Select if needed]
```

### Step 7: Save
Click **"Save"** button

---

## Result ✓

Your product now:
- ✅ Appears in all selected categories
- ✅ Is filterable by primary category
- ✅ Syncs primary category automatically
- ✅ Shows in frontend category pages

---

## Editing Existing Products

1. Go to **Store → Hampers**
2. Click product name
3. Scroll to **"📂 Categories & Organization"**
4. Update checkboxes
5. Click **"Save"**

---

## Viewing Products by Category

1. Go to **Store → Hampers** (list view)
2. Use **"By Categories"** filter on right
3. Select a category
4. See all products in that category

---

## Category Management

### View Categories
**Admin → Store → Categories**

### Add New Category
1. Click **"+ Add Category"**
2. Name: `[Category Name]`
3. Parent: `[Select parent if subcategory]`
4. Position: `[Order number]`
5. Save

### Reorder Categories
1. Go to **Categories** list
2. Edit **Position** field
3. Save

---

## Example: Wedding Hamper

```
Product Name:      Premium Wedding Gift Hamper
Categories:        ✓ Wedding
                  ✓ Wedding Hampers
                  
Primary Category:  Wedding (automatic)
```

Now appears in:
- `/categories/wedding/` page
- `/categories/wedding-hampers/` page
- Category filter: Wedding
- Category filter: Wedding Hampers

---

## Symbol Guide

| Symbol | Meaning |
|--------|---------|
| `☐` | Parent category |
| `├─` | Child category (not last) |
| `↳` | Last child category |
| `[✓]` | Selected (checked) |
| `[ ]` | Unselected (unchecked) |

---

## Tips & Tricks

💡 **Select Multiple Categories**
- A wedding hamper can be in both "Wedding" and "Corporate" sections
- Just check multiple boxes!

💡 **Primary Category Matters**
- The first category you select becomes primary
- Used for admin filters and sorting
- Automatically updated when you save

💡 **Use Positions**
- Categories are ordered by position
- Lower numbers = appear first
- Helps organize your catalog

💡 **Organize Similar Products**
- Keep related products in same category
- Use subcategories for variants
- Makes browsing easier for customers

---

## Common Scenarios

### "I want this in both Wedding AND Corporate"
✓ Check both "Wedding → Wedding Hampers" AND "Corporate → ..."

### "Make this the bestseller"
✓ Check the "Is Bestseller" checkbox

### "Hide this product"
✓ Uncheck "Is Active"

### "Rearrange my categories"
✓ Edit positions in Categories list

### "Add a new category"
✓ Admin → Categories → Add

---

**Need help?** Check [CATEGORIES_IMPLEMENTATION.md](./CATEGORIES_IMPLEMENTATION.md) for detailed documentation.
