from odoo import models, fields, api

class ProductDiscountPromo(models.Model):
    _name = 'product.discount.promo'
    _description = 'Master Data Diskon & Promo'
    _order = 'id desc'

    name = fields.Char(string='Nama Diskon / Promo', required=True)
    code = fields.Char(string='Kode Promo', copy=False)
    active = fields.Boolean(string='Aktif', default=True)

    discount_type = fields.Selection([
        ('percentage', 'Persentase (%)'),
        ('fixed', 'Nominal (Rp)')
    ], string='Tipe Diskon', default='percentage', required=True)

    discount_value = fields.Float(string='Nilai Diskon', digits=(16, 0), required=True, default=0.0)

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

    def get_applicable_discount(self, product_tmpl, list_price=0.0):
        """Returns percentage discount float for a given product template"""
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
            if self.discount_type == 'percentage':
                return self.discount_value
            elif self.discount_type == 'fixed' and list_price > 0:
                return (self.discount_value / list_price) * 100.0
        return 0.0
