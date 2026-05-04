# Admin Interface Layout

## Product List View

```
┌────────────────────────────────────────────────────────────────────────────┐
│ Django Administration                                    [Logout] [User ▼] │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Store › Hampers                                          [+ Add Hamper]    │
│                                                                              │
│  Filter by:                                                                 │
│  □ Is Active                                                                │
│    ○ Yes   ○ No                                                             │
│                                                                             │
│  □ Is Featured                                                              │
│    ○ Yes   ○ No                                                             │
│                                                                             │
│  □ By Category                                                              │
│    □ Wedding                                                                │
│    □ Employee                                                               │
│    □ Corporate                                                              │
│                                                                             │
│  □ By Categories (Multi)                                                   │
│    □ Wedding Return Gifts                                                   │
│    □ Wedding Accessories                                                    │
│    □ Wedding Hampers                                                        │
│    □ Employee Welcome Kit                                                   │
│    □ Office Welcome Kit                                                     │
│    □ Corporate Christmas Gifts                                              │
│    □ Women's Day Gifts                                                      │
│    □ New Year Gifts                                                         │
│    □ Diwali Gifts                                                           │
│                                                                             │
├────────────────────────────────────────────────────────────────────────────┤
│ Name        SKU      Category  Min Qty  Active Featured Bestseller New    │
├────────────────────────────────────────────────────────────────────────────┤
│ Premium..   SKU1     Wedding    25     [✓]    [ ]      [✓]         [ ]  │
│ Deluxe..    SKU2     Corporate  25     [✓]    [ ]      [ ]         [✓]  │
│ Classic..   SKU3     Wedding    50     [✓]    [✓]      [ ]         [ ]  │
│                                                                             │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## Product Edit Form

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Change hamper - Premium Wedding Gift Hamper                  [Save] [Delete]│
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│ ▼ Basic Information                                                         │
│                                                                              │
│  Name *                                                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Premium Wedding Gift Hamper                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Slug *                                                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ premium-wedding-gift-hamper                                         │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Hamper Step *                                                              │
│  ┌──────────────────┐                                                      │
│  │ Base         ▼  │                                                       │
│  └──────────────────┘                                                      │
│                                                                             │
│  Cover Image                                                                │
│  [Choose File] [Preview]                                                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ ▼ 📂 Categories & Organization                                             │
│                                                                             │
│  Product Categories *                                                       │
│  Select which categories this product belongs to. The primary category     │
│  (first selected) is used for filtering and organization.                 │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │ [✓] ☐ Wedding                                                       │  │
│  │     [✓] ├─ Wedding Return Gifts                                     │  │
│  │     [ ] ├─ Wedding Accessories                                      │  │
│  │     [✓] ↳ Wedding Hampers                                           │  │
│  │                                                                      │  │
│  │ [ ] ☐ Employee                                                      │  │
│  │     [ ] ├─ Employee Welcome Kit                                     │  │
│  │     [ ] ↳ Office Welcome Kit                                        │  │
│  │                                                                      │  │
│  │ [ ] ☐ Corporate                                                     │  │
│  │     [ ] ├─ Corporate Christmas Gifts                                │  │
│  │     [ ] ├─ Women's Day Gifts                                        │  │
│  │     [ ] ├─ New Year Gifts                                           │  │
│  │     [ ] ↳ Diwali Gifts                                              │  │
│  │                                                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ ▼ Product Details                                                           │
│                                                                             │
│  Short Description                                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Premium collection for special wedding occasions                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Description                                                                │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Exquisite gift hamper curated for wedding celebrations...           │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Included Items                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │ Premium Chocolates (500g)                                           │  │
│  │ Dry Fruits Mix (300g)                                               │  │
│  │ Silk Towel Set                                                      │  │
│  │ Personalized Message Card                                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  Min Bulk Quantity *                                                        │
│  ┌────────────────────┐                                                    │
│  │ 25                │                                                     │
│  └────────────────────┘                                                    │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ ▶ Pricing (Collapsed)                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ ▼ Display Options                                                           │
│                                                                             │
│  [✓] Is Active                                                              │
│  [ ] Is Featured                                                            │
│  [ ] Is Event Special                                                       │
│  [✓] Is Bestseller                                                          │
│  [ ] Is New                                                                 │
│                                                                             │
│  Homepage Sections                                                          │
│  ┌────────────────────────────────────────┐  ┌────────────────────────┐   │
│  │ Available sections        >  Selected   │  │ Add all               │   │
│  │ - Wedding Specials                     │  │ Remove all            │   │
│  │ - Corporate Welcome                    │  │                       │   │
│  │ - Event Hampers                        │  │ Featured Hampers (✓)  │   │
│  │ - Festival Collection                  │  │                       │   │
│  │                                        │  │                       │   │
│  └────────────────────────────────────────┘  └────────────────────────┘   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ [Save and add another]  [Save and continue editing]  [Save]  [Delete]     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Category Management

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Django Administration                                    [Logout] [User ▼] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Store › Categories                                      [+ Add Category]   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│ Image  Category              Parent      Slug                 Position Active│
├─────────────────────────────────────────────────────────────────────────────┤
│ [img]  ☐ Wedding             —           wedding              1    [✓]     │
│        ├─ Wedding Return...  Wedding     wedding-return...    1    [✓]     │
│        ├─ Wedding Accessor.. Wedding     wedding-accessori..  2    [✓]     │
│        ↳ Wedding Hampers     Wedding     wedding-hampers      3    [✓]     │
│                                                                             │
│ [img]  ☐ Employee            —           employee             2    [✓]     │
│        ├─ Employee Welcome.. Employee    employee-welcome..   1    [✓]     │
│        ↳ Office Welcome Kit  Employee    office-welcome-kit   2    [✓]     │
│                                                                             │
│ [img]  ☐ Corporate           —           corporate            3    [✓]     │
│        ├─ Corporate Christ..  Corporate  corporate-christm..  1    [✓]     │
│        ├─ Women's Day Gifts  Corporate  womens-day-gifts      2    [✓]     │
│        ├─ New Year Gifts     Corporate  new-year-gifts        3    [✓]     │
│        ↳ Diwali Gifts        Corporate  diwali-gifts          4    [✓]     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Features Highlighted

### ✅ Hierarchical Widget
```
☐ Parent Category (Bold)
  ├─ Child 1 (Indented)
  ├─ Child 2 (Indented)
  ↳ Child 3 (Last child)
```

### ✅ Multi-Select Checkboxes
```
[✓] Wedding (Selected)
    [✓] Wedding Return Gifts (Selected)
    [ ] Wedding Accessories (Not selected)
    [✓] Wedding Hampers (Selected)

[First selected = Primary category]
```

### ✅ Clean Fieldset Organization
```
1. Basic Information
   └─ Name, Slug, Step, Image

2. 📂 Categories & Organization  ← Highlighted!
   └─ Categories (Hierarchical)

3. Product Details
   └─ Description, Items, Qty

4. Pricing
   └─ Price, Label (Collapsible)

5. Display Options
   └─ Active, Featured, etc.
```

---

## Interaction Flow

```
1. Admin opens product form
   ↓
2. Scrolls to "📂 Categories & Organization"
   ↓
3. Sees hierarchical category tree
   ↓
4. Checks relevant categories
   ↓
5. Saves product
   ↓
6. System auto-sets primary category (first checked)
   ↓
7. Product appears in all selected categories on frontend
   ↓
8. Filterable by category in admin
```

---

## Responsive Design

The hierarchical widget adapts to screen size:

**Desktop (Wide)**
```
☐ Wedding
  ├─ Wedding Return Gifts
  ├─ Wedding Accessories
  ↳ Wedding Hampers
```

**Tablet (Medium)**
```
☐ Wedding
  ├─ Wedding Return...
  ├─ Wedding Accessor...
  ↳ Wedding Hampers
```

**Mobile (Narrow)**
```
☐ Wedding
  ├─ Wedding Re...
  ├─ Wedding Ac...
  ↳ Wedding Ha...
```

All checkboxes remain fully functional and easy to tap.

---

**Visual Guide Last Updated:** May 3, 2026
