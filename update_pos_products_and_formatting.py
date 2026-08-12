#!/usr/bin/env python3
import sys
import os
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = sys.argv[1] if len(sys.argv) > 1 else 'odoo-big-frozen'
CONFIG_FILE = '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf'

# Category mapping definitions
CATEGORIES_DEF = {
    "Olahan Daging Sapi": {
        "bg_main": (139, 0, 0),         # Dark Red / Maroon
        "bg_gradient": (80, 0, 0),
        "accent": (255, 215, 0),        # Gold
        "tag": "OLAHAN DAGING SAPI",
        "icon": "BEEF"
    },
    "Olahan Daging Ayam": {
        "bg_main": (217, 119, 6),       # Warm Amber
        "bg_gradient": (146, 64, 14),
        "accent": (254, 240, 138),      # Light Gold
        "tag": "OLAHAN DAGING AYAM",
        "icon": "CHICKEN"
    },
    "Olahan Ikan & Seafood": {
        "bg_main": (2, 132, 199),       # Ocean Cyan
        "bg_gradient": (12, 74, 110),
        "accent": (186, 230, 253),      # Ice Blue
        "tag": "OLAHAN IKAN & SEAFOOD",
        "icon": "SEAFOOD"
    },
    "Dimsum": {
        "bg_main": (5, 150, 105),       # Jade Green
        "bg_gradient": (6, 78, 59),
        "accent": (167, 243, 208),      # Soft Mint
        "tag": "DIMSUM BEKU",
        "icon": "DIMSUM"
    },
    "Kentang & Snack": {
        "bg_main": (202, 138, 4),       # Golden Yellow
        "bg_gradient": (113, 63, 18),
        "accent": (254, 240, 138),
        "tag": "KENTANG & SNACK",
        "icon": "SNACK"
    },
    "Bumbu & Pelengkap": {
        "bg_main": (220, 38, 38),       # Chili Red
        "bg_gradient": (127, 29, 29),
        "accent": (254, 202, 202),
        "tag": "BUMBU & SAUS",
        "icon": "SAUCE"
    }
}

# Mapping keywords in product names to category
PRODUCT_CAT_RULES = [
    # Olahan Daging Sapi
    (["daging slice", "bakso sapi", "sosis sapi", "bakso urat", "bratwurst", "shortplate", "bernardi bakso sapi", "bernardi sosis sapi"], "Olahan Daging Sapi"),
    
    # Olahan Daging Ayam
    (["nugget", "sosis ayam", "bakso ayam", "chicken", "karage", "karaage", "katsu", "popcorn", "strip", "wings", "champ", "fiesta", "kanzler"], "Olahan Daging Ayam"),
    
    # Olahan Ikan & Seafood
    (["fish", "crab", "seafood", "ebi", "tempura", "shrimp", "otak-otak", "scallop", "dori", "udang kupas", "salmon ball", "cedea"], "Olahan Ikan & Seafood"),
    
    # Dimsum
    (["dimsum", "siomay", "hakau", "gyoza"], "Dimsum"),
    
    # Kentang & Snack
    (["french fries", "fries", "potato", "hashbrown", "mydibel"], "Kentang & Snack"),
    
    # Bumbu & Pelengkap
    (["saus", "mayonaise", "bumbu"], "Bumbu & Pelengkap")
]

def determine_category(product_name):
    name_lower = product_name.lower()
    for keywords, cat_name in PRODUCT_CAT_RULES:
        if any(kw in name_lower for kw in keywords):
            return cat_name
    return "Olahan Daging Ayam"  # fallback default

def create_product_image(product_name, category_name):
    cat_style = CATEGORIES_DEF.get(category_name, CATEGORIES_DEF["Olahan Daging Ayam"])
    
    img_size = (512, 512)
    img = Image.new('RGB', img_size, color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient background card
    bg_main = cat_style["bg_main"]
    bg_grad = cat_style["bg_gradient"]
    
    for y in range(20, 492):
        r = int(bg_main[0] + (bg_grad[0] - bg_main[0]) * (y - 20) / 472)
        g = int(bg_main[1] + (bg_grad[1] - bg_main[1]) * (y - 20) / 472)
        b = int(bg_main[2] + (bg_grad[2] - bg_main[2]) * (y - 20) / 472)
        draw.line([(20, y), (492, y)], fill=(r, g, b))
        
    # Outer Border
    draw.rectangle([20, 20, 492, 492], outline=cat_style["accent"], width=5)
    
    # Category Tag Header Pill
    draw.rectangle([40, 40, 472, 85], fill=(0, 0, 0, 100), outline=cat_style["accent"], width=2)
    
    # Central Food Graphics / Circles
    draw.ellipse([176, 130, 336, 290], fill=(255, 255, 255, 40), outline=cat_style["accent"], width=4)
    draw.ellipse([196, 150, 316, 270], fill=cat_style["accent"])
    
    # Draw Inner Food Icon Shape
    icon_type = cat_style["icon"]
    if icon_type == "BEEF":
        # Draw steak/meatball shapes
        draw.ellipse([216, 170, 260, 214], fill=(120, 30, 30))
        draw.ellipse([252, 206, 296, 250], fill=(100, 20, 20))
        draw.ellipse([220, 220, 254, 254], fill=(140, 40, 40))
    elif icon_type == "CHICKEN":
        # Draw drumstick / nugget shapes
        draw.polygon([(230, 180), (280, 170), (290, 220), (250, 250)], fill=(234, 88, 12))
        draw.ellipse([216, 216, 266, 256], fill=(251, 146, 60))
    elif icon_type == "SEAFOOD":
        # Draw fish / prawn curve
        draw.polygon([(220, 210), (270, 170), (290, 210), (250, 250)], fill=(2, 132, 199))
        draw.ellipse([240, 180, 280, 220], fill=(56, 189, 248))
    elif icon_type == "DIMSUM":
        # Draw steamer dumpling shape
        draw.ellipse([216, 180, 296, 240], fill=(244, 244, 245))
        draw.ellipse([236, 170, 276, 195], fill=(253, 224, 71))
    elif icon_type == "SNACK":
        # Draw french fries sticks
        draw.rectangle([230, 170, 245, 250], fill=(253, 224, 71))
        draw.rectangle([250, 160, 265, 250], fill=(250, 204, 21))
        draw.rectangle([270, 175, 285, 250], fill=(234, 179, 8))
    else:
        # Sauce bottle / dip
        draw.rectangle([240, 160, 270, 240], fill=(220, 38, 38))
        draw.polygon([(245, 160), (265, 160), (255, 140)], fill=(254, 240, 138))

    # Try to load TTF font or use default font
    try:
        font_tag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_weight = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 18)
    except Exception:
        font_tag = font_title = font_weight = ImageFont.load_default()

    # Draw Category Tag Text
    tag_text = cat_style["tag"]
    draw.text((256, 62), tag_text, fill=(255, 255, 255), font=font_tag, anchor="mm")

    # Product Title Text Box at Bottom
    draw.rectangle([35, 320, 477, 430], fill=(0, 0, 0, 160), outline=cat_style["accent"], width=2)

    # Wrap title if long
    words = product_name.split()
    line1 = ""
    line2 = ""
    for w in words:
        if len(line1 + " " + w) < 22:
            line1 += (" " if line1 else "") + w
        else:
            line2 += (" " if line2 else "") + w
            
    if line2:
        draw.text((256, 355), line1, fill=(255, 255, 255), font=font_title, anchor="mm")
        draw.text((256, 395), line2, fill=cat_style["accent"], font=font_title, anchor="mm")
    else:
        draw.text((256, 375), line1, fill=(255, 255, 255), font=font_title, anchor="mm")

    # Weight / Pack Badge at Bottom Right
    weight_str = "FROZEN FOOD"
    for w_kw in ["500g", "1kg", "2kg", "250g", "450g", "375g", "15 pcs", "10 pcs"]:
        if w_kw.lower() in product_name.lower():
            weight_str = w_kw.upper()
            break
            
    draw.rectangle([320, 440, 472, 480], fill=cat_style["accent"], outline=(255, 255, 255), width=2)
    draw.text((396, 460), weight_str, fill=(0, 0, 0), font=font_weight, anchor="mm")

    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def run():
    print("=================================================================")
    print("      UPDATING ODOO POS PRODUCTS, CATEGORIES, & CURRENCY        ")
    print("=================================================================")
    
    odoo.tools.config.parse_config(['-c', CONFIG_FILE, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})

        # -------------------------------------------------------------
        # 1. PRICE & QTY FORMATTING: REMOVE DECIMALS (,00)
        # -------------------------------------------------------------
        print("\n[1/4] Updating Currencies, Decimal Precision, and UoM to remove decimal places (,00)...")
        cr.execute("""
            UPDATE res_currency 
            SET decimal_places = 0, rounding = 1.0, symbol = 'Rp', position = 'before' 
            WHERE name IN ('USD', 'IDR')
        """)
        cr.execute("UPDATE decimal_precision SET digits = 0")
        cr.execute("UPDATE uom_uom SET rounding = 1.0")
        env.invalidate_all()

        idr = env['res.currency'].with_context(active_test=False).search([('name', '=', 'IDR')], limit=1)
        if idr:
            idr.write({'active': True})
            
        company = env['res.company'].search([], limit=1)
        if idr:
            cr.execute("UPDATE res_company SET currency_id = %s WHERE id = %s", (idr.id, company.id))
            
        pricelists = env['product.pricelist'].search([])
        for pl in pricelists:
            if idr:
                pl.write({'currency_id': idr.id})

        print(f"      Currency, Decimal Precision (0 digits), and UoM (1.0 rounding) formatting updated!")
        print(f"      Sample Price Format (32200): {idr.format(32200.0)}")

        # -------------------------------------------------------------
        # 2. CREATE INTERNAL & POS CATEGORIES
        # -------------------------------------------------------------
        print("\n[2/4] Setting up Internal Categories and POS Categories...")
        int_cat_map = {}
        pos_cat_map = {}

        for cat_name in CATEGORIES_DEF.keys():
            # Internal Category
            int_cat = env['product.category'].search([('name', '=', cat_name)], limit=1)
            if not int_cat:
                int_cat = env['product.category'].create({'name': cat_name})
            int_cat_map[cat_name] = int_cat

            # POS Category
            pos_cat = env['pos.category'].search([('name', '=', cat_name)], limit=1)
            if not pos_cat:
                pos_cat = env['pos.category'].create({'name': cat_name})
            pos_cat_map[cat_name] = pos_cat

        print(f"      {len(int_cat_map)} Categories ready (Internal & POS).")

        # -------------------------------------------------------------
        # 3. CATEGORIZE ALL PRODUCTS & ASSIGN IMAGES
        # -------------------------------------------------------------
        print("\n[3/4] Categorizing products and generating product photos...")
        
        # Get all frozen food product templates
        all_templates = env['product.template'].search([('sale_ok', '=', True)])
        updated_count = 0

        for tmpl in all_templates:
            # Check if this is a frozen food item
            is_frozen = any(kw in tmpl.name.lower() for kw in [
                'nugget', 'sosis', 'bakso', 'ayam', 'sapi', 'fish', 'crab', 'seafood', 
                'ebi', 'dimsum', 'siomay', 'hakau', 'gyoza', 'fries', 'potato', 
                'hashbrown', 'chicken', 'tempura', 'shrimp', 'otak', 'scallop', 
                'sauce', 'saus', 'mayonaise', 'bumbu', 'dori', 'udang', 'bernardi', 
                'champ', 'cedea', 'fiesta', 'kanzler', 'mydibel', 'slice', 'shortplate'
            ])

            if is_frozen:
                cat_name = determine_category(tmpl.name)
                int_cat = int_cat_map[cat_name]
                pos_cat = pos_cat_map[cat_name]

                # Generate Product Image
                img_b64 = create_product_image(tmpl.name, cat_name)

                # Write to template
                tmpl.write({
                    'categ_id': int_cat.id,
                    'pos_categ_ids': [(6, 0, [pos_cat.id])],
                    'available_in_pos': True,
                    'image_1920': img_b64
                })
                updated_count += 1
                print(f"      Product [{tmpl.id:3d}] {tmpl.name:<42} -> {cat_name:<22} (Image set)")
            else:
                pass

        print(f"\n      Total Frozen Food Products Updated: {updated_count}")

        # -------------------------------------------------------------
        # 4. CONFIGURE POS CONFIGURATIONS
        # -------------------------------------------------------------
        print("\n[4/4] Updating POS Configurations...")
        # Close draft opening_control sessions to allow editing pos.config and ensure stop_at is set
        cr.execute("UPDATE pos_session SET state = 'closed', stop_at = COALESCE(stop_at, write_date, NOW()) WHERE state IN ('opening_control', 'opened')")
        env.invalidate_all()

        pos_configs = env['pos.config'].search([])
        all_pos_cat_ids = [c.id for c in pos_cat_map.values()]

        for pos in pos_configs:
            pos.write({
                'limit_categories': False,
                'iface_available_categ_ids': [(6, 0, all_pos_cat_ids)]
            })
            print(f"      POS Configuration [{pos.name}] updated (limit_categories=False, {len(all_pos_cat_ids)} categories available).")

        cr.commit()
        print("\n=================================================================")
        print(" SUCCESS: ALL CHANGES COMMITTED TO ODOO DATABASE successfully! ")
        print("=================================================================")

if __name__ == '__main__':
    run()
