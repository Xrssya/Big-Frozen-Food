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
        print("=== POPULATING BANKS & BANK ACCOUNTS FOR CONTACTS ===")

        # 1. Create / Ensure Major Indonesian Banks
        banks_def = [
            ("Bank Central Asia (BCA)", "BCA", "CENAIDJA"),
            ("Bank Mandiri", "MANDIRI", "BMRIIDJA"),
            ("Bank Negara Indonesia (BNI)", "BNI", "BBNIIDJA"),
            ("Bank Rakyat Indonesia (BRI)", "BRI", "BRINIDJA"),
            ("Bank Syariah Indonesia (BSI)", "BSI", "BSIMIDJA"),
            ("Bank CIMB Niaga", "CIMB", "BNIAIDJA"),
        ]

        bank_map = {}
        for b_name, b_code, b_bic in banks_def:
            bank = env['res.bank'].search([('name', '=', b_name)], limit=1)
            if not bank:
                bank = env['res.bank'].create({
                    'name': b_name,
                    'bic': b_bic,
                })
            bank_map[b_name] = bank
        print(f" {len(bank_map)} Major Indonesian Banks ready.")

        # 2. Add Bank Accounts for Company (Big Frozen Food)
        company_partner = env['res.company'].search([], limit=1).partner_id
        if company_partner:
            for b_name, acc_num in [("Bank Central Asia (BCA)", "8730998877"), ("Bank Mandiri", "1420099887700")]:
                bank_obj = bank_map[b_name]
                acc = env['res.partner.bank'].search([('partner_id', '=', company_partner.id), ('bank_id', '=', bank_obj.id)], limit=1)
                if not acc:
                    env['res.partner.bank'].create({
                        'partner_id': company_partner.id,
                        'bank_id': bank_obj.id,
                        'acc_number': acc_num,
                        'acc_holder_name': 'PT Big Frozen Food',
                    })
            print(f" Company bank accounts created for {company_partner.name}.")

        # 3. Add Bank Accounts for Vendors & Customers
        partners = env['res.partner'].search([('is_company', '=', True)])
        print(f" Populating bank accounts for {len(partners)} company contacts...")

        bank_list = list(bank_map.values())

        acc_count = 0
        for p in partners:
            # Check if partner already has a bank account
            existing_accs = env['res.partner.bank'].search([('partner_id', '=', p.id)])
            if not existing_accs:
                # Assign 1 or 2 random bank accounts
                num_accs = random.choice([1, 2])
                for idx in range(num_accs):
                    chosen_bank = bank_list[(p.id + idx) % len(bank_list)]
                    
                    # Generate realistic 10-13 digit account number
                    if "BCA" in chosen_bank.name:
                        acc_no = f"{random.randint(100, 899)}{random.randint(100000, 999999)}"
                    elif "Mandiri" in chosen_bank.name:
                        acc_no = f"14200{random.randint(1000000, 9999999)}"
                    elif "BNI" in chosen_bank.name:
                        acc_no = f"0891{random.randint(100000, 999999)}"
                    elif "BRI" in chosen_bank.name:
                        acc_no = f"002301{random.randint(100000, 999999)}"
                    else:
                        acc_no = f"701{random.randint(10000000, 99999999)}"

                    env['res.partner.bank'].create({
                        'partner_id': p.id,
                        'bank_id': chosen_bank.id,
                        'acc_number': acc_no,
                        'acc_holder_name': p.name,
                    })
                    acc_count += 1

        cr.commit()
        print(f"=== SUCCESS: CREATED {acc_count} BANK ACCOUNTS ACROSS ALL CONTACTS ===")

if __name__ == '__main__':
    run()
