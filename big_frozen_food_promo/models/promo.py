from odoo import models, fields, api

class ProductDiscountPromo(models.Model):
    _name = 'product.discount.promo'
    _inherit = ['pos.load.mixin']
    _description = 'Master Data Diskon & Promo'
    _order = 'id desc'

    @api.model
    def _load_pos_data_domain(self, data):
        return [('active', '=', True)]

    @api.model
    def _load_pos_data_fields(self, config_id):
        return [
            'id', 'name', 'code', 'promo_type', 'discount_type', 'discount_value',
            'min_qty_buy', 'free_qty', 'reward_product_id', 'apply_on',
            'product_ids', 'category_id', 'date_start', 'date_end'
        ]

    name = fields.Char(string='Nama Diskon / Promo', required=True)
    code = fields.Char(string='Kode Promo', copy=False)
    active = fields.Boolean(string='Aktif', default=True)

    promo_type = fields.Selection([
        ('discount', 'Diskon Reguler (% / Rp)'),
        ('buy_x_get_y', 'Beli X Gratis Y')
    ], string='Tipe Promo', default='discount', required=True)

    discount_type = fields.Selection([
        ('percentage', 'Persentase (%)'),
        ('fixed', 'Nominal (Rp)')
    ], string='Tipe Diskon', default='percentage')

    discount_value = fields.Float(string='Nilai Diskon', digits=(16, 0), default=0.0)

    min_qty_buy = fields.Integer(
        string='Syarat Beli (Qty X)',
        default=2,
        help='Jumlah minimum unit yang harus dibeli untuk mendapatkan item gratis.'
    )

    free_qty = fields.Integer(
        string='Jumlah Gratis (Qty Y)',
        default=1,
        help='Jumlah unit yang didapatkan secara gratis per syarat kuantitas.'
    )

    reward_product_id = fields.Many2one(
        'product.template',
        string='Produk Hadiah / Gratisan',
        help='Kosongkan jika produk gratisan sama dengan produk yang dibeli.'
    )

    apply_on = fields.Selection([
        ('all', 'Semua Produk'),
        ('product', 'Produk Spesifik'),
        ('category', 'Kategori Produk')
    ], string='Berlaku Untuk', default='product', required=True)

    product_ids = fields.Many2many(
        'product.template',
        'promo_product_rel',
        'promo_id',
        'product_tmpl_id',
        string='Daftar Produk'
    )

    category_id = fields.Many2one('product.category', string='Kategori Produk')

    date_start = fields.Datetime(string='Tanggal Mulai')
    date_end = fields.Datetime(string='Tanggal Selesai')
    notes = fields.Text(string='Catatan / Syarat & Ketentuan')

    product_count = fields.Integer(string='Jumlah Produk', compute='_compute_product_count')

    @api.depends('apply_on', 'product_ids', 'category_id')
    def _compute_product_count(self):
        for rec in self:
            if rec.apply_on == 'product':
                rec.product_count = len(rec.product_ids)
            elif rec.apply_on == 'category' and rec.category_id:
                rec.product_count = self.env['product.template'].search_count([('categ_id', '=', rec.category_id.id)])
            elif rec.apply_on == 'all':
                rec.product_count = self.env['product.template'].search_count([])
            else:
                rec.product_count = 0

    def action_view_products(self):
        self.ensure_one()
        domain = []
        if self.apply_on == 'product':
            domain = [('id', 'in', self.product_ids.ids)]
        elif self.apply_on == 'category' and self.category_id:
            domain = [('categ_id', '=', self.category_id.id)]
        return {
            'name': 'Produk Promo',
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'view_mode': 'kanban,list,form',
            'domain': domain,
        }

    def get_applicable_discount(self, product_tmpl, list_price=0.0, qty=1.0):
        """Returns percentage discount float for a given product template and quantity"""
        self.ensure_one()
        if not self.active:
            return 0.0
        now = fields.Datetime.now()
        if self.date_start and now < self.date_start:
            return 0.0
        if self.date_end and now > self.date_end:
            return 0.0

        is_match = False
        if self.apply_on == 'all':
            is_match = True
        elif self.apply_on == 'product' and product_tmpl.id in self.product_ids.ids:
            is_match = True
        elif self.apply_on == 'category' and self.category_id and product_tmpl.categ_id.id == self.category_id.id:
            is_match = True

        if is_match:
            if self.promo_type == 'discount':
                if self.discount_type == 'percentage':
                    return self.discount_value
                elif self.discount_type == 'fixed' and list_price > 0:
                    return (self.discount_value / list_price) * 100.0
            elif self.promo_type == 'buy_x_get_y':
                min_buy = self.min_qty_buy or 2.0
                free_item = self.free_qty or 1.0
                package_size = min_buy + free_item
                if package_size > 0 and qty >= package_size:
                    sets = int(qty // package_size)
                    total_free = sets * free_item
                    return (total_free / qty) * 100.0
        return 0.0

