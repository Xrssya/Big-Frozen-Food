# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    min_stock_alert_qty = fields.Float(
        string='Batas Stok Minimum (Alert)',
        default=10.0,
        help='Batas jumlah stok minimum di mana sistem akan memberikan notifikasi stok menipis.',
        digits=(16, 0)
    )

    min_stock_reserve_qty = fields.Float(
        string='Batas Stok Tahan (Minimum Penjualan)',
        default=0.0,
        help='Batas jumlah stok fisik minimum yang harus tersisa di gudang. Transaksi akan diblokir jika sisa stok kurang dari nilai ini.',
        digits=(16, 0)
    )

    allow_negative_stock = fields.Boolean(
        string='Izinkan Stok Minus',
        default=False,
        help='Jika diaktifkan, produk ini tetap dapat dijual meskipun stok di tangan habis/0.'
    )

    pcs_per_box = fields.Integer(
        string='Isi per Kardus / Box',
        default=12,
        help='Jumlah pack/pcs satuan dalam 1 box atau kardus.'
    )

    is_low_stock = fields.Boolean(
        string='Stok Menipis',
        compute='_compute_is_low_stock',
        search='_search_is_low_stock',
        help='True jika jumlah stok fisik di tangan (qty_available) kurang dari atau sama dengan batas stok minimum.'
    )

    stock_status = fields.Selection([
        ('available', 'Stok Cukup'),
        ('low', 'Stok Menipis'),
        ('empty', 'Stok Habis')
    ], string='Status Stok', compute='_compute_stock_status', search='_search_stock_status', store=False)

    @api.depends('qty_available', 'min_stock_alert_qty', 'min_stock_reserve_qty', 'is_storable')
    def _compute_stock_status(self):
        for template in self:
            if not template.is_storable:
                template.stock_status = 'available'
            elif template.qty_available <= template.min_stock_reserve_qty:
                template.stock_status = 'empty'
            elif template.qty_available <= template.min_stock_alert_qty:
                template.stock_status = 'low'
            else:
                template.stock_status = 'available'

    def _search_stock_status(self, operator, value):
        if operator not in ('=', '!='):
            return []
        query = """
            SELECT pt.id
            FROM product_template pt
            JOIN product_product pp ON pp.product_tmpl_id = pt.id
            LEFT JOIN stock_quant sq ON sq.product_id = pp.id AND sq.location_id IN (
                SELECT id FROM stock_location WHERE usage = 'internal'
            )
            GROUP BY pt.id, pt.min_stock_alert_qty, pt.min_stock_reserve_qty, pt.is_storable
            HAVING (
                CASE
                    WHEN pt.is_storable = FALSE THEN 'available'
                    WHEN COALESCE(SUM(sq.quantity), 0) <= COALESCE(pt.min_stock_reserve_qty, 0) THEN 'empty'
                    WHEN COALESCE(SUM(sq.quantity), 0) <= COALESCE(pt.min_stock_alert_qty, 10) THEN 'low'
                    ELSE 'available'
                END
            ) = %s
        """
        self.env.cr.execute(query, (value,))
        matched_ids = [row[0] for row in self.env.cr.fetchall()]
        want = (operator == '=')
        return [('id', 'in' if want else 'not in', matched_ids)]

    @api.depends('qty_available', 'min_stock_alert_qty')
    def _compute_is_low_stock(self):
        for template in self:
            template.is_low_stock = (template.qty_available <= template.min_stock_alert_qty)

    def _search_is_low_stock(self, operator, value):
        if operator not in ('=', '!='):
            return []
        query = """
            SELECT pt.id
            FROM product_template pt
            JOIN product_product pp ON pp.product_tmpl_id = pt.id
            LEFT JOIN stock_quant sq ON sq.product_id = pp.id AND sq.location_id IN (
                SELECT id FROM stock_location WHERE usage = 'internal'
            )
            GROUP BY pt.id, pt.min_stock_alert_qty
            HAVING COALESCE(SUM(sq.quantity), 0) <= COALESCE(pt.min_stock_alert_qty, 10)
        """
        self.env.cr.execute(query)
        low_stock_ids = [row[0] for row in self.env.cr.fetchall()]
        want_low = (operator == '=' and value) or (operator == '!=' and not value)
        return [('id', 'in' if want_low else 'not in', low_stock_ids)]


class ProductProduct(models.Model):
    _inherit = 'product.product'

    min_stock_alert_qty = fields.Float(
        related='product_tmpl_id.min_stock_alert_qty',
        readonly=False,
        store=True
    )
    min_stock_reserve_qty = fields.Float(
        related='product_tmpl_id.min_stock_reserve_qty',
        readonly=False,
        store=True
    )
    allow_negative_stock = fields.Boolean(
        related='product_tmpl_id.allow_negative_stock',
        readonly=False,
        store=True
    )
    pcs_per_box = fields.Integer(
        related='product_tmpl_id.pcs_per_box',
        readonly=False,
        store=True
    )
    is_low_stock = fields.Boolean(
        related='product_tmpl_id.is_low_stock',
        store=False
    )
    stock_status = fields.Selection(
        related='product_tmpl_id.stock_status',
        store=False
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        for field_name in ['qty_available', 'min_stock_alert_qty', 'min_stock_reserve_qty', 'pcs_per_box', 'allow_negative_stock']:
            if field_name not in fields_list:
                fields_list.append(field_name)
        return fields_list

    @api.model
    def add_pos_product_stock(self, product_id, added_qty, picking_type_id=False):
        """Allows POS Admin/Manager to quickly add/adjust stock directly from POS interface."""
        return self.update_pos_product_stock_and_price(product_id, added_qty=added_qty, picking_type_id=picking_type_id)

    @api.model
    def update_pos_product_stock_and_price(self, product_id, added_qty=0.0, new_price=None, picking_type_id=False):
        """Allows POS Admin/Manager to update product stock and/or selling price directly from POS."""
        if not self.env.user.has_group('point_of_sale.group_pos_manager'):
            raise UserError(_("Akses Ditolak: Hanya Admin / POS Manager yang diizinkan mengubah stok dan harga dari kasir!"))

        product = self.browse(product_id)
        if not product:
            raise UserError(_("Produk tidak ditemukan!"))

        messages = []
        new_qty_available = product.qty_available
        updated_price = product.lst_price

        # 1. Update Selling Price if provided
        if new_price is not None:
            new_price = float(new_price)
            if new_price < 0:
                raise UserError(_("Harga produk tidak boleh kurang dari 0!"))
            
            # Sudo write to bypass restriction for POS Manager
            product.product_tmpl_id.sudo().write({'list_price': new_price})
            updated_price = new_price
            messages.append(_("Harga baru: Rp %s") % f"{int(new_price):,}")

        # 2. Update Stock if added_qty > 0
        added_qty = float(added_qty or 0.0)
        if added_qty > 0:
            location = False
            if picking_type_id:
                try:
                    pt_id = int(picking_type_id)
                    pt = self.env['stock.picking.type'].browse(pt_id)
                    if pt and pt.exists() and pt.default_location_src_id:
                        location = pt.default_location_src_id
                except (ValueError, TypeError):
                    pass

            if not location:
                pos_config = self.env['pos.config'].search([('company_id', '=', self.env.company.id)], limit=1)
                if pos_config and pos_config.picking_type_id and pos_config.picking_type_id.default_location_src_id:
                    location = pos_config.picking_type_id.default_location_src_id

            if not location:
                warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
                if warehouse and warehouse.lot_stock_id:
                    location = warehouse.lot_stock_id

            if not location:
                location = self.env['stock.location'].search([
                    ('usage', '=', 'internal'),
                    ('company_id', 'in', [self.env.company.id, False])
                ], order='id asc', limit=1)

            if not location:
                raise UserError(_("Lokasi stok gudang internal tidak ditemukan!"))

            quant = self.env['stock.quant'].search([
                ('product_id', '=', product.id),
                ('location_id', '=', location.id)
            ], limit=1)

            current_qty = quant.quantity if quant else 0.0
            new_qty = current_qty + added_qty

            self.env['stock.quant'].with_context(inventory_mode=True).create({
                'product_id': product.id,
                'location_id': location.id,
                'inventory_quantity': new_qty,
            }).action_apply_inventory()

            product.invalidate_recordset(['qty_available'])
            new_qty_available = product.with_context(location=location.id).qty_available
            messages.append(_("Stok ditambahkan: +%s pack (Total: %s pack)") % (int(added_qty), int(new_qty_available)))

        if not messages:
            return {'success': True, 'product_id': product.id, 'new_qty_available': new_qty_available, 'new_price': updated_price, 'message': _("Tidak ada perubahan yang disimpan.")}

        msg_str = _("Perubahan '%s' berhasil disimpan:\n• ") % product.display_name + "\n• ".join(messages)

        return {
            'success': True,
            'product_id': product.id,
            'added_qty': added_qty,
            'new_qty_available': new_qty_available,
            'new_price': updated_price,
            'message': msg_str
        }



