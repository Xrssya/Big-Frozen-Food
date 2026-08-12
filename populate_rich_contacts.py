#!/usr/bin/env python3
import sys
import random

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-c', '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== COMPLETING ALL IMPORTANT FIELDS FOR CONTACTS ===")

        # Fetch State (Jawa Timur) & Country (Indonesia)
        indonesia = env['res.country'].search([('code', '=', 'ID')], limit=1)
        jawatimur = env['res.country.state'].search([('name', '=', 'Jawa Timur')], limit=1)

        # Payment Terms
        term_immediate = env['account.payment.term'].search([('name', 'ilike', 'Immediate')], limit=1) or env.ref('account.account_payment_term_immediate', raise_if_not_found=False)
        term_15days = env['account.payment.term'].search([('name', 'ilike', '15')], limit=1) or env.ref('account.account_payment_term_15days', raise_if_not_found=False)
        term_30days = env['account.payment.term'].search([('name', 'ilike', '30')], limit=1) or env.ref('account.account_payment_term_30days', raise_if_not_found=False)

        # Sample PIC Names
        pic_first_names = ["Budi", "Siti", "Ahmad", "Dewi", "Eko", "Rina", "Hendra", "Maya", "Agus", "Fitri", "Dedi", "Indah", "Rizal", "Novi", "Hasan"]
        pic_last_names = ["Santoso", "Wibowo", "Kusuma", "Pratama", "Wijaya", "Setiawan", "Utami", "Saputra", "Lestari", "Hidayat"]
        pic_titles = ["Manajer Pengadaan", "Supervisor Logistik", "Bagian Keuangan / Finance", "Kepala Toko", "General Manager"]

        city_data = {
            "Pasuruan": ("Jl. Raya Soekarno Hatta No. ", "67111", "0343"),
            "Bangil": ("Jl. Alun-Alun Utara No. ", "67153", "0343"),
            "Pandaan": ("Jl. Raya Bypass Pandaan No. ", "67156", "0343"),
            "Malang": ("Jl. Sukarno Hatta Ruko Frozen No. ", "65141", "0341"),
            "Sidoarjo": ("Jl. Ahmad Yani No. ", "61211", "031"),
            "Surabaya": ("Jl. Rungkut Industri Raya No. ", "60251", "031"),
            "Gresik": ("Jl. Veteran No. ", "61111", "031"),
            "Mojokerto": ("Jl. Gajah Mada No. ", "61311", "0321"),
            "Jombang": ("Jl. KH Wahid Hasyim No. ", "61411", "0321"),
            "Probolinggo": ("Jl. Panglima Sudirman No. ", "67211", "0335"),
        }

        # 1. Update Company (Big Frozen Food)
        company_partner = env['res.company'].search([], limit=1).partner_id
        if company_partner:
            company_partner.write({
                'street': 'Jl. Industri Cold Storage No. 123',
                'street2': 'Kawasan Industri Pier',
                'city': 'Pasuruan',
                'state_id': jawatimur.id if jawatimur else False,
                'country_id': indonesia.id if indonesia else False,
                'zip': '67111',
                'phone': '0343-421999',
                'mobile': '0811-3000-8888',
                'email': 'info@bigfrozenfood.co.id',
                'website': 'https://www.bigfrozenfood.co.id',
                'vat': '01.234.567.8-651.000',
            })
            print(" Company contact profile fully updated.")

        # 2. Update Vendors (Suppliers)
        vendors = env['res.partner'].search([('supplier_rank', '>', 0)])
        for idx, v in enumerate(vendors):
            v_name_clean = v.name.lower().replace(" ", "").replace(".", "")
            v.write({
                'street': f'Jl. Industri Pangan & Cold Chain No. {idx * 12 + 10}',
                'street2': 'Kawasan Industri Rungkut Phase II',
                'city': 'Surabaya',
                'state_id': jawatimur.id if jawatimur else False,
                'country_id': indonesia.id if indonesia else False,
                'zip': '60293',
                'phone': f'031-894500{idx+1}',
                'mobile': f'0812-3344-556{idx+1}',
                'email': f'sales@{v_name_clean}.co.id',
                'website': f'https://www.{v_name_clean}.co.id',
                'vat': f'02.{idx+1}34.567.8-602.000',
                'property_supplier_payment_term_id': term_30days.id if term_30days else False,
            })

            # Create Child Contact / PIC for Vendor
            pic_name = f"{random.choice(pic_first_names)} {random.choice(pic_last_names)}"
            if not env['res.partner'].search([('parent_id', '=', v.id)], limit=1):
                env['res.partner'].create({
                    'parent_id': v.id,
                    'type': 'contact',
                    'name': pic_name,
                    'function': random.choice(pic_titles),
                    'phone': v.phone,
                    'mobile': f'0813-9988-776{idx+1}',
                    'email': f'{pic_name.lower().replace(" ", ".")}@{v_name_clean}.co.id',
                })
        print(f" {len(vendors)} Vendors fully completed with addresses, NPWP, and PIC contacts.")

        # 3. Update Resellers & Agens
        b2b_partners = env['res.partner'].search([('is_company', '=', True), ('supplier_rank', '=', 0), ('name', '!=', 'Big Frozen Food')])
        for idx, p in enumerate(b2b_partners):
            p_city = p.city if p.city in city_data else random.choice(list(city_data.keys()))
            street_prefix, zip_code, area_code = city_data[p_city]
            p_name_clean = p.name.lower().replace(" ", "").replace(".", "")

            is_agen = "Agen" in p.name
            payment_term = term_30days if is_agen else term_15days

            p.write({
                'street': f'{street_prefix}{idx * 5 + 12}',
                'street2': f'Ruko Central Frozen Blok A-{idx+1}',
                'city': p_city,
                'state_id': jawatimur.id if jawatimur else False,
                'country_id': indonesia.id if indonesia else False,
                'zip': zip_code,
                'phone': f'{area_code}-77880{idx+1}',
                'mobile': f'0812-7766-554{idx+1}',
                'email': f'order@{p_name_clean}.com',
                'website': f'https://www.{p_name_clean}.com',
                'vat': f'03.{idx+1}88.999.0-{zip_code[:3]}.000',
                'property_payment_term_id': payment_term.id if payment_term else False,
            })

            # Create Child Contact / PIC for Customer
            pic_name = f"{random.choice(pic_first_names)} {random.choice(pic_last_names)}"
            if not env['res.partner'].search([('parent_id', '=', p.id)], limit=1):
                env['res.partner'].create({
                    'parent_id': p.id,
                    'type': 'contact',
                    'name': pic_name,
                    'function': random.choice(pic_titles),
                    'phone': p.phone,
                    'mobile': f'0857-1122-334{idx+1}',
                    'email': f'{pic_name.lower().replace(" ", ".")}@{p_name_clean}.com',
                })
        print(f" {len(b2b_partners)} Customer Companies (Resellers & Agens) completed with full addresses, NPWP, Payment Terms, and PIC contacts.")

        # 4. Update Retail / Individual Customers (Umum)
        umum_partners = env['res.partner'].search([('is_company', '=', False), ('parent_id', '=', False), ('name', 'ilike', 'Umum')])
        for idx, u in enumerate(umum_partners):
            u.write({
                'street': f'Jl. Pahlawan No. {idx+15}',
                'city': 'Pasuruan',
                'state_id': jawatimur.id if jawatimur else False,
                'country_id': indonesia.id if indonesia else False,
                'zip': '67111',
                'mobile': f'0819-0011-223{idx+1}',
                'property_payment_term_id': term_immediate.id if term_immediate else False,
            })

        cr.commit()
        print("=== SUCCESS: ALL CONTACT FIELDS COMPLETED PRODUCTION-READY ===")

if __name__ == '__main__':
    run()
