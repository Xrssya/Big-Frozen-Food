#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/adi-purwanto/developer/odoo18')
import odoo
from odoo import api, fields, SUPERUSER_ID

DB_NAME = 'odoo-big-frozen'
CONFIG_PATH = '/home/adi-purwanto/developer/odoo/ubig.food/Big-Frozen-Food/big_frozen_food.conf'

def close_sessions():
    odoo.tools.config.parse_config(['-c', CONFIG_PATH, '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        open_sessions = env['pos.session'].search([('state', '!=', 'closed')])
        if not open_sessions:
            print("Tidak ada sesi POS yang terbuka.")
            return

        for session in open_sessions:
            print(f"Menutup sesi POS: {session.name} (User: {session.user_id.name}, State: {session.state})")
            try:
                if session.state == 'opened':
                    session.action_pos_session_closing_control()
                if session.state in ('closing_control', 'closing_control'):
                    session.action_pos_session_close()
            except Exception as e:
                print(f"Mengubah status sesi {session.name} secara langsung ke 'closed'...")
                session.write({'state': 'closed', 'stop_at': fields.Datetime.now()})
            print(f"Sesi {session.name} berhasil ditutup.")
        cr.commit()

if __name__ == '__main__':
    close_sessions()
