# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockTransferRequest(models.Model):
    _name = 'stock.transfer.request'
    _description = 'Permintaan Restock Darurat antar Cabang / Gudang'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, id desc'

    name = fields.Char(
        string='Nomor Pengajuan',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Baru')
    )

    request_date = fields.Datetime(
        string='Tanggal Pengajuan',
        default=fields.Datetime.now,
        required=True
    )

    requested_by_id = fields.Many2one(
        'res.users',
        string='Diajukan Oleh',
        default=lambda self: self.env.user,
        required=True,
        readonly=True
    )

    source_location_id = fields.Many2one(
        'stock.location',
        string='Lokasi Asal (Gudang/Cabang Pengirim)',
        domain="[('usage', '=', 'internal')]",
        required=True,
        help='Lokasi stok barang yang akan diambil.'
    )

    dest_location_id = fields.Many2one(
        'stock.location',
        string='Lokasi Tujuan (Toko/Cabang Penerima)',
        domain="[('usage', '=', 'internal')]",
        required=True,
        help='Lokasi tempat barang frozen food akan disimpan setelah diterima.'
    )

    priority = fields.Selection([
        ('0', 'Biasa'),
        ('1', '⚠️ Penting'),
        ('2', '🔥 🔴 Darurat (Stok Kosong)')
    ], string='Tingkat Prioritas', default='1', required=True)

    state = fields.Selection([
        ('draft', 'Draft / Pengajuan'),
        ('submitted', 'Menunggu Persetujuan'),
        ('approved', 'Disetujui (Transfer Terbuat)'),
        ('done', 'Selesai / Barang Diterima'),
        ('cancelled', 'Dibatalkan')
    ], string='Status Pengajuan', default='draft', tracking=True)

    line_ids = fields.One2many(
        'stock.transfer.request.line',
        'request_id',
        string='Daftar Produk Restock',
        copy=True
    )

    notes = fields.Text(
        string='Alasan / Catatan Pengajuan',
        help='Contoh: Stok Bakso Ayam di Toko A habis akibat lonjakan pembeli akhir pekan.'
    )

    picking_id = fields.Many2one(
        'stock.picking',
        string='Dokumen Transfer Odoo',
        readonly=True,
        copy=False
    )

    picking_count = fields.Integer(
        string='Jumlah Transfer',
        compute='_compute_picking_count'
    )

    @api.depends('picking_id')
    def _compute_picking_count(self):
        for req in self:
            req.picking_count = 1 if req.picking_id else 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Baru')) == _('Baru'):
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.transfer.request') or _('REQ-RESTOCK-001')
        return super().create(vals_list)

    def action_submit(self):
        for req in self:
            if not req.line_ids:
                raise UserError(_("Harap tambahkan minimal 1 produk yang ingin di-restock!"))
            req.write({'state': 'submitted'})

            stock_manager_group = self.env.ref('stock.group_stock_manager', raise_if_not_found=False)
            stock_managers = self.env['res.users'].search([
                ('groups_id', 'in', stock_manager_group.id)
            ]) if stock_manager_group else self.env['res.users'].search([('id', '=', 1)])

            todo_activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            activity_type_id = todo_activity_type.id if todo_activity_type else False

            priority_label = dict(req._fields['priority'].selection).get(req.priority, '')
            msg = _("Pengajuan Restock Darurat Baru: <b>%s</b> (%s)<br/>Dari: %s → Ke: %s") % (
                req.name, priority_label, req.source_location_id.display_name, req.dest_location_id.display_name
            )

            model_id = self.env['ir.model'].search([('model', '=', 'stock.transfer.request')], limit=1).id

            for manager in stock_managers:
                self.env['mail.activity'].create({
                    'activity_type_id': activity_type_id,
                    'note': msg,
                    'summary': f'Persetujuan Restock Darurat: {req.name}',
                    'user_id': manager.id,
                    'res_id': req.id,
                    'res_model_id': model_id,
                })
        return True

    def action_approve(self):
        picking_type_obj = self.env['stock.picking.type']
        for req in self:
            if req.state != 'submitted':
                raise UserError(_("Pengajuan harus dalam status 'Menunggu Persetujuan'!"))
            if not req.line_ids:
                raise UserError(_("Daftar produk restock kosong!"))

            picking_type = picking_type_obj.search([
                ('code', '=', 'internal'),
                ('warehouse_id.lot_stock_id', '=', req.source_location_id.id)
            ], limit=1) or picking_type_obj.search([('code', '=', 'internal')], limit=1) or picking_type_obj.search([], limit=1)

            if not picking_type:
                raise UserError(_("Tipe operasi Internal Transfer tidak ditemukan!"))

            moves = []
            for line in req.line_ids:
                moves.append((0, 0, {
                    'name': f"Restock {line.product_id.name}",
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty_requested,
                    'product_uom': line.uom_id.id or line.product_id.uom_id.id,
                    'location_id': req.source_location_id.id,
                    'location_dest_id': req.dest_location_id.id,
                }))

            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': req.source_location_id.id,
                'location_dest_id': req.dest_location_id.id,
                'move_ids_without_package': moves,
                'origin': req.name,
            })
            picking.action_confirm()

            req.write({
                'state': 'approved',
                'picking_id': picking.id
            })
        return True

    def action_cancel(self):
        for req in self:
            if req.picking_id and req.picking_id.state == 'done':
                raise UserError(_("Tidak dapat membatalkan pengajuan yang transfernya sudah Selesai!"))
            if req.picking_id and req.picking_id.state != 'cancel':
                req.picking_id.action_cancel()
            req.write({'state': 'cancelled'})
        return True

    def action_view_picking(self):
        self.ensure_one()
        if not self.picking_id:
            return {}
        return {
            'name': _('Dokumen Transfer Internal'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.picking_id.id,
            'type': 'ir.actions.act_window',
        }


class StockTransferRequestLine(models.Model):
    _name = 'stock.transfer.request.line'
    _description = 'Detail Produk Permintaan Restock'

    request_id = fields.Many2one(
        'stock.transfer.request',
        string='Pengajuan Restock',
        ondelete='cascade',
        required=True
    )

    product_id = fields.Many2one(
        'product.product',
        string='Produk Frozen Food',
        required=True,
        domain="[('is_storable', '=', True)]"
    )

    qty_requested = fields.Float(
        string='Jumlah Diminta',
        default=1.0,
        required=True,
        digits='Product Unit of Measure'
    )

    qty_box = fields.Float(
        string='Jml Box/Kardus',
        digits='Product Unit of Measure',
        default=0.0,
        help='Jumlah kardus/box yang diminta.'
    )

    pcs_per_box = fields.Integer(
        related='product_id.pcs_per_box',
        string='Isi per Box',
        readonly=True
    )

    uom_id = fields.Many2one(
        'uom.uom',
        string='Satuan (UoM)',
        related='product_id.uom_id',
        readonly=True
    )

    qty_available_source = fields.Float(
        string='Stok Tersedia di Pengirim',
        compute='_compute_qty_available_source',
        help='Jumlah stok fisik saat ini yang tersedia di gudang/lokasi asal.'
    )

    @api.onchange('qty_box')
    def _onchange_qty_box(self):
        """When user inputs Box quantity, calculate total Pack/Satuan quantity."""
        for line in self:
            ratio = line.pcs_per_box or (line.product_id.pcs_per_box if line.product_id else 12) or 1
            if line.qty_box and ratio > 0:
                line.qty_requested = line.qty_box * ratio

    @api.onchange('qty_requested')
    def _onchange_qty_requested_sync_box(self):
        """When user inputs Pack quantity, update Box quantity."""
        for line in self:
            ratio = line.pcs_per_box or (line.product_id.pcs_per_box if line.product_id else 12) or 1
            if ratio > 0 and line.qty_requested:
                line.qty_box = round(line.qty_requested / ratio, 2)

    @api.onchange('product_id')
    def _onchange_product_id_sync_box(self):
        """Initialize Box quantity when selecting a product."""
        for line in self:
            if line.product_id:
                ratio = line.product_id.pcs_per_box or 12
                if line.qty_requested:
                    line.qty_box = round(line.qty_requested / ratio, 2) if ratio > 0 else 0.0
                else:
                    line.qty_box = 1.0
                    line.qty_requested = float(ratio)

    @api.depends('product_id', 'request_id.source_location_id')
    def _compute_qty_available_source(self):
        for line in self:
            if not line.product_id or not line.request_id.source_location_id:
                line.qty_available_source = 0.0
                continue
            quants = self.env['stock.quant'].search([
                ('product_id', '=', line.product_id.id),
                ('location_id', '=', line.request_id.source_location_id.id)
            ])
            line.qty_available_source = sum(quants.mapped('quantity'))

