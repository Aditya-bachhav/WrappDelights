# CSV Import Template for Products

Save this as `products_sample.csv` and fill with your data.

## Column Structure:
- **name**: Product name (required)
- **category**: Category name (will be created if doesn't exist)
- **sku**: Stock keeping unit (optional, auto-generated if empty)
- **short_description**: Brief description (max 150 chars recommended)
- **specifications**: Bullet-point specs (use line breaks in Excel/Google Sheets)
- **tags**: Comma-separated tags (not yet implemented in current model)

## Usage:

```bash
python manage.py import_products products.csv
```

## Sample Data:

```csv
name,category,sku,short_description,specifications,tags
"Steel Water Bottle - 500ml","Drinkware","STEEL-500","Premium stainless steel water bottle with copper lining","• 500ml capacity
• Double-wall insulation
• BPA-free
• Keeps cold 24hrs, hot 12hrs","drinkware,steel,insulated"
"Bamboo Desk Organizer","Office Supplies","DESK-BAMB-01","Eco-friendly bamboo desk organizer with 6 compartments","• 100% natural bamboo
• 6 compartments
• Non-slip base
• Dimensions: 30x15x10cm","office,bamboo,eco-friendly"
"Corporate Gift Box - Premium","Corporate Gifts","CORP-PREM-01","Luxury gift box with branded items for executive gifting","• Customizable branding
• Premium packaging
• Includes: pen, diary, bottle
• MOQ: 25 units","corporate,premium,gift-box"
```

## Notes:
- Use quotes around values containing commas
- For multi-line specifications, use actual line breaks in Excel
- Empty SKU will auto-generate as "SKU0001", "SKU0002", etc.
- Categories are created automatically if they don't exist
