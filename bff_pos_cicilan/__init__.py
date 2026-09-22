# -*- coding: utf-8 -*-
from . import models
from . import wizard


def _post_init_hook(env):
    """
    Otomatis membuat & mendaftarkan POS Payment Method 'Cicilan'
    ke seluruh POS Config di database setelah modul di-install.
    """
    companies = env['res.company'].search([])
    for company in companies:
        pm_cicilan = env['pos.payment.method'].search([
            ('company_id', '=', company.id),
            ('name', 'ilike', 'Cicilan'),
        ], limit=1)

        if not pm_cicilan:
            pm_cicilan = env['pos.payment.method'].create({
                'name': 'Cicilan',
                'company_id': company.id,
                'is_cicilan': True,
                'split_transactions': True,
                'journal_id': False,  # Customer Account / Pay Later
            })
        else:
            pm_cicilan.write({
                'is_cicilan': True,
            })

        pos_configs = env['pos.config'].search([('company_id', '=', company.id)])
        for cfg in pos_configs:
            if pm_cicilan.id not in cfg.payment_method_ids.ids:
                cfg.with_context(bypass_payment_method_ids_forbidden_change=True).write({
                    'payment_method_ids': [(4, pm_cicilan.id)]
                })
