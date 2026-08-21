# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, timedelta

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shelf_life_days = fields.Integer(
        string='Masa Simpan / Shelf Life (Hari)',
        default=180,
        help='Estimasi total hari kelayakan konsumsi produk frozen food sejak tanggal produksi.'
    )

    near_expiry_alert_days = fields.Integer(
        string='Ambang Peringatan Kadaluarsa (Hari)',
        default=30,
        help='Batas hari sebelum kadaluarsa untuk memicu peringatan stok mendekati expired (Near-Expiry Alert).'
    )

    auto_clearance_promo = fields.Boolean(
        string='Otomatis Diskon Cuci Gudang',
        default=True,
        help='Jika diaktifkan, produk yang mendekati kadaluarsa akan otomatis dimasukkan ke promo Diskon Cuci Gudang.'
    )

    clearance_discount_percent = fields.Float(
        string='Diskon Cuci Gudang (%)',
        default=25.0,
        digits=(16, 0),
        help='Persentase potongan harga untuk produk yang masuk dalam kategori cuci gudang (Near-Expiry Clearance Sale).'
    )

    is_near_expiry = fields.Boolean(
        string='Mendekati Kadaluarsa',
        compute='_compute_expiry_info',
        search='_search_is_near_expiry',
        help='True jika terdapat stok yang akan kadaluarsa dalam batas ambang hari peringatan.'
    )

    days_to_expiry = fields.Integer(
        string='Sisa Hari Kadaluarsa',
        compute='_compute_expiry_info',
        help='Jumlah hari tersisa hingga tanggal kadaluarsa terdekat.'
    )

    expiry_level = fields.Selection([
        ('safe', '🟢 Safe (>30 Hari)'),
        ('warning', '🟡 Warning (8-30 Hari)'),
        ('danger', '🔴 Danger (<7 Hari / Expired)')
    ], string='Tingkat Risiko Expired', compute='_compute_expiry_info', store=False)

    expiry_status = fields.Selection([
        ('safe', 'Kadaluarsa Aman'),
        ('near_expiry', 'Mendekati Expired (Cuci Gudang)'),
        ('expired', 'Kadaluarsa / Expired')
    ], string='Status Kadaluarsa', compute='_compute_expiry_info', search='_search_expiry_status', store=False)

    earliest_expiry_date = fields.Date(
        string='Kadaluarsa Terdekat',
        compute='_compute_expiry_info',
        inverse='_inverse_earliest_expiry_date',
        help='Tanggal kadaluarsa paling dekat dari lot/batch stok fisik yang tersedia.'
    )

    def _inverse_earliest_expiry_date(self):
        for template in self:
            if not template.earliest_expiry_date:
                continue
            lots = self.env['stock.lot'].search([
                ('product_id.product_tmpl_id', '=', template.id)
            ])

            exp_dt = datetime.combine(template.earliest_expiry_date, datetime.min.time())

            if lots:
                lots.write({'expiration_date': exp_dt})
            else:
                prod = template.product_variant_ids[:1] or self.env['product.product'].search([('product_tmpl_id', '=', template.id)], limit=1)
                if prod:
                    lot_name = f"LOT-{prod.id}-{template.earliest_expiry_date.strftime('%Y%m%d')}"
                    self.env['stock.lot'].create({
                        'name': lot_name,
                        'product_id': prod.id,
                        'expiration_date': exp_dt
                    })
            template._compute_expiry_info()

    @api.onchange('earliest_expiry_date')
    def _onchange_earliest_expiry_date(self):
        today = fields.Date.today()
        for template in self:
            if not template.earliest_expiry_date:
                template.is_near_expiry = False
                template.days_to_expiry = 999
                template.expiry_level = 'safe'
                template.expiry_status = 'safe'
                continue

            days_left = (template.earliest_expiry_date - today).days
            template.days_to_expiry = days_left
            alert_days = template.near_expiry_alert_days or 30

            if days_left <= 0:
                template.expiry_status = 'expired'
                template.expiry_level = 'danger'
                template.is_near_expiry = True
            elif days_left <= 7:
                template.expiry_status = 'near_expiry'
                template.expiry_level = 'danger'
                template.is_near_expiry = True
            elif days_left <= alert_days:
                template.expiry_status = 'near_expiry'
                template.expiry_level = 'warning'
                template.is_near_expiry = True
            else:
                template.expiry_status = 'safe'
                template.expiry_level = 'safe'
                template.is_near_expiry = False

    @api.depends('near_expiry_alert_days')
    def _compute_expiry_info(self):
        today = fields.Date.today()
        for template in self:
            lots = self.env['stock.lot'].search([
                ('product_id.product_tmpl_id', '=', template.id),
                ('expiration_date', '!=', False)
            ], order='expiration_date asc')

            if not lots:
                template.is_near_expiry = False
                template.days_to_expiry = 999
                template.expiry_level = 'safe'
                template.expiry_status = 'safe'
                template.earliest_expiry_date = False
                continue

            earliest_lot = lots[0]
            exp_date = fields.Date.to_date(earliest_lot.expiration_date)
            template.earliest_expiry_date = exp_date

            days_left = (exp_date - today).days
            template.days_to_expiry = days_left

            if days_left <= 0:
                template.expiry_status = 'expired'
                template.expiry_level = 'danger'
                template.is_near_expiry = True
            elif days_left <= 7:
                template.expiry_status = 'near_expiry'
                template.expiry_level = 'danger'
                template.is_near_expiry = True
            elif days_left <= template.near_expiry_alert_days:
                template.expiry_status = 'near_expiry'
                template.expiry_level = 'warning'
                template.is_near_expiry = True
            else:
                template.expiry_status = 'safe'
                template.expiry_level = 'safe'
                template.is_near_expiry = False

    def _search_is_near_expiry(self, operator, value):
        if operator not in ('=', '!='):
            return []
        templates = self.search([])
        matched_ids = [t.id for t in templates if (t.is_near_expiry and value) or (not t.is_near_expiry and not value)]
        return [('id', 'in', matched_ids)]

    def _search_expiry_status(self, operator, value):
        if operator not in ('=', '!='):
            return []
        templates = self.search([])
        matched_ids = [t.id for t in templates if (operator == '=' and t.expiry_status == value) or (operator == '!=' and t.expiry_status != value)]
        return [('id', 'in', matched_ids)]

    @api.model
    def cron_check_near_expiry_products(self):
        """Task harian untuk mengecek produk yang mendekati kadaluarsa
        dan mengirimkan notifikasi ke Manajer Gudang."""
        templates = self.search([])
        near_expiry_list = [t for t in templates if t.is_near_expiry]

        if near_expiry_list:
            stock_manager_group = self.env.ref('stock.group_stock_manager', raise_if_not_found=False)
            stock_managers = self.env['res.users'].search([
                ('groups_id', 'in', stock_manager_group.id)
            ]) if stock_manager_group else self.env['res.users'].search([('id', '=', 1)])

            if not stock_managers:
                stock_managers = self.env['res.users'].search([('id', '=', 1)])

            msg = _("<b>[PERINGATAN FEFO KADALUARSA]</b><br/>"
                    "Ditemukan <b>%d produk</b> frozen food mendekati masa kadaluarsa:<br/>") % len(near_expiry_list)

            for t in near_expiry_list:
                status_badge = "🔴 Kritis (< 7 Hari)" if t.expiry_level == 'danger' else "🟡 Peringatan (H-30)"
                exp_date_str = t.earliest_expiry_date.strftime('%d-%m-%Y') if t.earliest_expiry_date else "-"
                msg += f"• <b>{t.name}</b>: {status_badge} — Exp: {exp_date_str} (Sisa {t.days_to_expiry} Hari)<br/>"

            todo_activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            activity_type_id = todo_activity_type.id if todo_activity_type else False

            for user in stock_managers:
                self.env['mail.activity'].create({
                    'activity_type_id': activity_type_id,
                    'note': msg,
                    'summary': f'Laporan FEFO: {len(near_expiry_list)} Produk Mendekati Kadaluarsa',
                    'user_id': user.id,
                    'res_id': near_expiry_list[0].id,
                    'res_model_id': self.env.ref('product.model_product_template').id,
                })
        return True


class ProductProduct(models.Model):
    _inherit = 'product.product'

    shelf_life_days = fields.Integer(related='product_tmpl_id.shelf_life_days', readonly=False, store=True)
    near_expiry_alert_days = fields.Integer(related='product_tmpl_id.near_expiry_alert_days', readonly=False, store=True)
    auto_clearance_promo = fields.Boolean(related='product_tmpl_id.auto_clearance_promo', readonly=False, store=True)
    clearance_discount_percent = fields.Float(related='product_tmpl_id.clearance_discount_percent', readonly=False, store=True)
    is_near_expiry = fields.Boolean(related='product_tmpl_id.is_near_expiry', store=False)
    days_to_expiry = fields.Integer(related='product_tmpl_id.days_to_expiry', store=False)
    expiry_level = fields.Selection(related='product_tmpl_id.expiry_level', store=False)
    expiry_status = fields.Selection(related='product_tmpl_id.expiry_status', store=False)
    earliest_expiry_date = fields.Date(related='product_tmpl_id.earliest_expiry_date', readonly=False, store=False)

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        for field_name in [
            'shelf_life_days', 'near_expiry_alert_days', 'auto_clearance_promo',
            'clearance_discount_percent', 'is_near_expiry', 'days_to_expiry',
            'expiry_level', 'expiry_status', 'earliest_expiry_date'
        ]:
            if field_name not in fields_list:
                fields_list.append(field_name)
        return fields_list
