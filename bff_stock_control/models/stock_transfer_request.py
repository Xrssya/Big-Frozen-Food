# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockTransferRequest(models.Model):
    _name = 'stock.transfer.request'
    _description = 'Permintaan Restock / Transfer Antar Gudang'
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

    source_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Dari Gudang (Pengirim)',
        required=True,
        tracking=True,
        help='Gudang asal tempat produk frozen food akan diambil.'
    )

    dest_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Ke Gudang (Penerima)',
        required=True,
        tracking=True,
        help='Gudang tujuan tempat produk frozen food akan diterima.'
    )

    source_location_id = fields.Many2one(
        'stock.location',
        string='Lokasi Asal (Gudang/Cabang Pengirim)',
        domain="[('usage', '=', 'internal')]",
        required=True,
        help='Lokasi stok barang internal yang akan diambil.'
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
        ('approved', 'Disetujui (Picking Terbuat)'),
        ('in_transit', '🚚 Dalam Perjalanan'),
        ('done', '✓ Selesai / Barang Diterima'),
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

    out_picking_id = fields.Many2one(
        'stock.picking',
        string='Dokumen Pengiriman (Outbound)',
        readonly=True,
        copy=False
    )

    in_picking_id = fields.Many2one(
        'stock.picking',
        string='Dokumen Penerimaan (Inbound)',
        readonly=True,
        copy=False
    )

    picking_id = fields.Many2one(
        'stock.picking',
        string='Dokumen Transfer Utama',
        compute='_compute_picking_id',
        store=True,
        readonly=True,
        copy=False
    )

    out_picking_state = fields.Selection(
        related='out_picking_id.state',
        string='Status Outbound',
        readonly=True,
        store=True
    )

    in_picking_state = fields.Selection(
        related='in_picking_id.state',
        string='Status Inbound',
        readonly=True,
        store=True
    )

    out_picking_count = fields.Integer(
        string='Jumlah Transfer Outbound',
        compute='_compute_picking_counts'
    )

    in_picking_count = fields.Integer(
        string='Jumlah Transfer Inbound',
        compute='_compute_picking_counts'
    )

    picking_count = fields.Integer(
        string='Jumlah Transfer Total',
        compute='_compute_picking_counts'
    )

    @api.depends('out_picking_id', 'in_picking_id')
    def _compute_picking_id(self):
        for req in self:
            req.picking_id = req.out_picking_id or req.in_picking_id or False

    @api.depends('out_picking_id', 'in_picking_id')
    def _compute_picking_counts(self):
        for req in self:
            req.out_picking_count = 1 if req.out_picking_id else 0
            req.in_picking_count = 1 if req.in_picking_id else 0
            req.picking_count = (1 if req.out_picking_id else 0) + (1 if req.in_picking_id else 0)

    @api.onchange('source_warehouse_id')
    def _onchange_source_warehouse_id(self):
        if self.source_warehouse_id and self.source_warehouse_id.lot_stock_id:
            self.source_location_id = self.source_warehouse_id.lot_stock_id.id

    @api.onchange('dest_warehouse_id')
    def _onchange_dest_warehouse_id(self):
        if self.dest_warehouse_id and self.dest_warehouse_id.lot_stock_id:
            self.dest_location_id = self.dest_warehouse_id.lot_stock_id.id

    @api.constrains('source_warehouse_id', 'dest_warehouse_id')
    def _check_warehouses(self):
        for req in self:
            if not req.source_warehouse_id or not req.dest_warehouse_id:
                continue
            if req.source_warehouse_id == req.dest_warehouse_id:
                raise ValidationError(_("Gudang Asal dan Gudang Tujuan tidak boleh sama!"))
            if not req.source_warehouse_id.company_id or not req.dest_warehouse_id.company_id:
                raise ValidationError(_("Gudang Asal dan Gudang Tujuan harus terhubung dengan Perusahaan (Company) yang valid."))

    @api.constrains('line_ids', 'source_location_id', 'dest_location_id')
    def _check_lines_and_locations(self):
        for req in self:
            if req.state in ('draft', 'submitted') and not req.line_ids:
                raise ValidationError(_("Harap tambahkan minimal 1 produk yang ingin di-transfer!"))
            for line in req.line_ids:
                if line.qty_requested <= 0:
                    raise ValidationError(_("Kuantitas produk '%s' harus lebih besar dari 0.") % line.product_id.display_name)
            if req.source_warehouse_id and req.source_location_id != req.source_warehouse_id.lot_stock_id:
                raise ValidationError(_("Lokasi Asal harus sesuai dengan lokasi stok utama Gudang Asal '%s'.") % req.source_warehouse_id.display_name)
            if req.dest_warehouse_id and req.dest_location_id != req.dest_warehouse_id.lot_stock_id:
                raise ValidationError(_("Lokasi Tujuan harus sesuai dengan lokasi stok utama Gudang Tujuan '%s'.") % req.dest_warehouse_id.display_name)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Baru')) == _('Baru'):
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.transfer.request') or _('REQ-RESTOCK-001')
            if vals.get('source_warehouse_id') and not vals.get('source_location_id'):
                wh = self.env['stock.warehouse'].browse(vals['source_warehouse_id'])
                if wh and wh.lot_stock_id:
                    vals['source_location_id'] = wh.lot_stock_id.id
            if vals.get('dest_warehouse_id') and not vals.get('dest_location_id'):
                wh = self.env['stock.warehouse'].browse(vals['dest_warehouse_id'])
                if wh and wh.lot_stock_id:
                    vals['dest_location_id'] = wh.lot_stock_id.id
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('source_warehouse_id') and not vals.get('source_location_id'):
            wh = self.env['stock.warehouse'].browse(vals['source_warehouse_id'])
            if wh and wh.lot_stock_id:
                vals['source_location_id'] = wh.lot_stock_id.id
        if vals.get('dest_warehouse_id') and not vals.get('dest_location_id'):
            wh = self.env['stock.warehouse'].browse(vals['dest_warehouse_id'])
            if wh and wh.lot_stock_id:
                vals['dest_location_id'] = wh.lot_stock_id.id
        return super().write(vals)

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
            msg = _("Pengajuan Restock Transfer Gudang Baru: <b>%s</b> (%s)<br/>Dari: %s → Ke: %s") % (
                req.name, priority_label, req.source_warehouse_id.display_name, req.dest_warehouse_id.display_name
            )

            model_id = self.env['ir.model'].search([('model', '=', 'stock.transfer.request')], limit=1).id

            for manager in stock_managers:
                self.env['mail.activity'].create({
                    'activity_type_id': activity_type_id,
                    'note': msg,
                    'summary': f'Persetujuan Restock Transfer: {req.name}',
                    'user_id': manager.id,
                    'res_id': req.id,
                    'res_model_id': model_id,
                })
        return True

    def action_approve(self):
        picking_type_obj = self.env['stock.picking.type'].sudo()
        transit_location = self.env['stock.location'].sudo().search([('usage', '=', 'transit')], limit=1)
        if not transit_location:
            raise UserError(_("Lokasi Inter-company Transit ('usage = transit') tidak ditemukan pada database."))

        for req in self:
            if req.state != 'submitted':
                raise UserError(_("Pengajuan harus dalam status 'Menunggu Persetujuan'!"))
            if not req.line_ids:
                raise UserError(_("Daftar produk restock kosong!"))

            source_wh = req.sudo().source_warehouse_id
            dest_wh = req.sudo().dest_warehouse_id
            source_company = source_wh.company_id
            dest_company = dest_wh.company_id

            # 1. Resolve Outbound Picking Type for Source Warehouse (Delivery Orders / code='outgoing')
            outbound_type = picking_type_obj.search([
                ('code', '=', 'outgoing'),
                ('warehouse_id', '=', source_wh.id),
                ('company_id', '=', source_company.id)
            ], limit=1) or picking_type_obj.search([
                ('code', '=', 'outgoing'),
                ('company_id', '=', source_company.id)
            ], limit=1)

            if not outbound_type:
                raise UserError(_(
                    "Tipe Operasi Pengiriman / Outbound (Delivery Orders) tidak ditemukan untuk Gudang Asal '%s' (Perusahaan: '%s'). "
                    "Harap periksa konfigurasi Tipe Operasi di menu Inventory > Configuration > Operation Types."
                ) % (source_wh.display_name, source_company.display_name))

            # 2. Resolve Inbound Picking Type for Destination Warehouse (Receipts / code='incoming')
            inbound_type = picking_type_obj.search([
                ('code', '=', 'incoming'),
                ('warehouse_id', '=', dest_wh.id),
                ('company_id', '=', dest_company.id)
            ], limit=1) or picking_type_obj.search([
                ('code', '=', 'incoming'),
                ('company_id', '=', dest_company.id)
            ], limit=1)

            if not inbound_type:
                raise UserError(_(
                    "Tipe Operasi Penerimaan / Inbound (Receipts) tidak ditemukan untuk Gudang Tujuan '%s' (Perusahaan: '%s'). "
                    "Harap periksa konfigurasi Tipe Operasi di menu Inventory > Configuration > Operation Types."
                ) % (dest_wh.display_name, dest_company.display_name))

            # 3. Build Stock Moves for Outbound (Source Location -> Global Transit)
            outbound_moves = []
            for line in req.line_ids:
                outbound_moves.append((0, 0, {
                    'name': f"Transfer Outbound: {line.product_id.name}",
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty_requested,
                    'product_uom': line.uom_id.id or line.product_id.uom_id.id,
                    'location_id': req.source_location_id.id,
                    'location_dest_id': transit_location.id,
                    'company_id': source_company.id,
                }))

            out_picking = self.env['stock.picking'].sudo().create({
                'picking_type_id': outbound_type.id,
                'location_id': req.source_location_id.id,
                'location_dest_id': transit_location.id,
                'company_id': source_company.id,
                'move_ids_without_package': outbound_moves,
                'origin': req.name,
            })
            out_picking.sudo().action_confirm()
            out_picking.sudo().action_assign()

            # 4. Build Stock Moves for Inbound (Global Transit -> Dest Location)
            inbound_moves = []
            for line in req.line_ids:
                inbound_moves.append((0, 0, {
                    'name': f"Transfer Inbound: {line.product_id.name}",
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty_requested,
                    'product_uom': line.uom_id.id or line.product_id.uom_id.id,
                    'location_id': transit_location.id,
                    'location_dest_id': req.dest_location_id.id,
                    'company_id': dest_company.id,
                }))

            in_picking = self.env['stock.picking'].sudo().create({
                'picking_type_id': inbound_type.id,
                'location_id': transit_location.id,
                'location_dest_id': req.dest_location_id.id,
                'company_id': dest_company.id,
                'move_ids_without_package': inbound_moves,
                'origin': req.name,
            })
            in_picking.sudo().action_confirm()
            in_picking.sudo().action_assign()

            req.sudo().write({
                'state': 'approved',
                'out_picking_id': out_picking.id,
                'in_picking_id': in_picking.id,
            })
            req.message_post(body=_("Pengajuan Transfer disetujui. Dokumen Transfer Keluar (%s) & Transfer Masuk (%s) telah dibuat.") % (
                out_picking.name, in_picking.name
            ))
        return True

    def action_cancel(self):
        for req in self:
            if req.state in ('done', 'in_transit'):
                raise UserError(_("Pengajuan transfer yang barangnya sudah Dalam Perjalanan atau Selesai tidak dapat dibatalkan langsung. Gunakan fitur Retur jika barang perlu dikembalikan."))
            if req.out_picking_id and req.out_picking_id.state not in ('done', 'cancel'):
                req.out_picking_id.action_cancel()
            if req.in_picking_id and req.in_picking_id.state not in ('done', 'cancel'):
                req.in_picking_id.action_cancel()
            req.write({'state': 'cancelled'})
            req.message_post(body=_("Pengajuan Transfer dibatalkan oleh %s.") % self.env.user.name)
        return True

    def action_draft(self):
        for req in self:
            if req.state != 'cancelled':
                raise UserError(_("Hanya pengajuan dengan status 'Dibatalkan' yang dapat dikembalikan ke status Draft."))
            req.write({
                'state': 'draft',
                'out_picking_id': False,
                'in_picking_id': False,
            })
            req.message_post(body=_("Pengajuan Transfer dikembalikan ke status Draft oleh %s.") % self.env.user.name)
        return True


    def action_return_transit_to_source(self):
        """Recovery mechanism when shipment is in transit but needs to be returned to source warehouse."""
        self.ensure_one()
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise UserError(_("Hanya Manager Inventory yang berhak mengembalikan barang transit ke Gudang Asal."))

        if self.state != 'in_transit':
            raise UserError(_("Fitur Retur Transit hanya dapat digunakan ketika barang dalam status 'Dalam Perjalanan'."))

        transit_location = self.env['stock.location'].search([('usage', '=', 'transit')], limit=1)
        source_company = self.source_warehouse_id.company_id

        # Cancel Inbound picking if still active
        if self.in_picking_id and self.in_picking_id.state not in ('done', 'cancel'):
            self.in_picking_id.action_cancel()

        # Resolve Outbound Picking Type for Return (Receipt / Incoming in source warehouse)
        return_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id', '=', self.source_warehouse_id.id),
            ('company_id', '=', source_company.id)
        ], limit=1) or self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('company_id', '=', source_company.id)
        ], limit=1)

        return_moves = []
        for line in self.line_ids:
            shipped_qty = line.qty_shipped or line.qty_requested
            if shipped_qty > 0:
                return_moves.append((0, 0, {
                    'name': f"Retur Transit: {line.product_id.name}",
                    'product_id': line.product_id.id,
                    'product_uom_qty': shipped_qty,
                    'product_uom': line.uom_id.id or line.product_id.uom_id.id,
                    'location_id': transit_location.id,
                    'location_dest_id': self.source_location_id.id,
                    'company_id': source_company.id,
                }))

        if return_moves and return_type:
            return_picking = self.env['stock.picking'].create({
                'picking_type_id': return_type.id,
                'location_id': transit_location.id,
                'location_dest_id': self.source_location_id.id,
                'company_id': source_company.id,
                'move_ids_without_package': return_moves,
                'origin': _("Retur Transit %s") % self.name,
            })
            return_picking.action_confirm()
            return_picking.action_assign()
            for move in return_picking.move_ids:
                move.quantity = move.product_uom_qty
                move.picked = True
            return_picking.button_validate()

        self.write({'state': 'cancelled'})
        self.message_post(body=_("Pengiriman barang di transit berhasil dikembalikan ke Gudang Asal %s oleh %s.") % (
            self.source_warehouse_id.display_name, self.env.user.name
        ))
        return True

    def _sync_transfer_request_state(self):
        """Automated state machine & partial backorder sync logic."""
        for req in self:
            if req.state in ('draft', 'submitted', 'cancelled'):
                continue

            out_done = (req.out_picking_id and req.out_picking_id.state == 'done')
            in_done = (req.in_picking_id and req.in_picking_id.state == 'done')
            out_cancelled = (req.out_picking_id and req.out_picking_id.state == 'cancel')

            if out_done and not in_done:
                # 1. Partial / Backorder Sync: Update Inbound Picking move demand quantity to match actual Outbound shipped quantity
                if req.in_picking_id and req.in_picking_id.state not in ('done', 'cancel'):
                    for in_move in req.in_picking_id.move_ids:
                        out_moves = req.out_picking_id.move_ids.filtered(lambda m: m.product_id == in_move.product_id)
                        actual_shipped = sum(out_moves.mapped('quantity')) if any(out_moves.mapped('quantity')) else sum(out_moves.mapped('product_uom_qty'))
                        if actual_shipped > 0 and in_move.product_uom_qty != actual_shipped:
                            in_move.write({
                                'product_uom_qty': actual_shipped,
                                'quantity': actual_shipped,
                            })
                if req.state != 'in_transit':
                    req.write({'state': 'in_transit'})

            elif out_done and in_done:
                if req.state != 'done':
                    req.write({'state': 'done'})

            elif out_cancelled and not in_done:
                if req.in_picking_id and req.in_picking_id.state not in ('done', 'cancel'):
                    req.in_picking_id.action_cancel()
                if req.state != 'cancelled':
                    req.write({'state': 'cancelled'})

    def action_view_out_picking(self):
        self.ensure_one()
        if not self.out_picking_id:
            return {}
        return {
            'name': _('Dokumen Transfer Keluar (Outbound)'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.out_picking_id.id,
            'type': 'ir.actions.act_window',
        }

    def action_view_in_picking(self):
        self.ensure_one()
        if not self.in_picking_id:
            return {}
        return {
            'name': _('Dokumen Transfer Masuk (Inbound)'),
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'res_id': self.in_picking_id.id,
            'type': 'ir.actions.act_window',
        }

    def action_view_picking(self):
        self.ensure_one()
        if self.out_picking_id:
            return self.action_view_out_picking()
        elif self.in_picking_id:
            return self.action_view_in_picking()
        return {}


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

    qty_shipped = fields.Float(
        string='Jumlah Dikirim (Outbound)',
        compute='_compute_shipped_received',
        store=True,
        digits='Product Unit of Measure'
    )

    qty_received = fields.Float(
        string='Jumlah Diterima (Inbound)',
        compute='_compute_shipped_received',
        store=True,
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
        digits=(16, 0),
        help='Jumlah stok fisik saat ini yang tersedia di gudang/lokasi asal.'
    )

    @api.depends('request_id.out_picking_id.state', 'request_id.in_picking_id.state', 'request_id.out_picking_id.move_ids.quantity', 'request_id.in_picking_id.move_ids.quantity')
    def _compute_shipped_received(self):
        for line in self:
            shipped = 0.0
            received = 0.0
            req = line.request_id
            if req and req.out_picking_id and req.out_picking_id.state == 'done':
                out_moves = req.out_picking_id.move_ids.filtered(lambda m: m.product_id == line.product_id)
                shipped = sum(out_moves.mapped('quantity')) or sum(out_moves.mapped('product_uom_qty'))
            if req and req.in_picking_id and req.in_picking_id.state == 'done':
                in_moves = req.in_picking_id.move_ids.filtered(lambda m: m.product_id == line.product_id)
                received = sum(in_moves.mapped('quantity')) or sum(in_moves.mapped('product_uom_qty'))
            line.qty_shipped = shipped
            line.qty_received = received

    @api.onchange('qty_box')
    def _onchange_qty_box(self):
        for line in self:
            ratio = line.pcs_per_box or (line.product_id.pcs_per_box if line.product_id else 12) or 1
            if line.qty_box and ratio > 0:
                line.qty_requested = line.qty_box * ratio

    @api.onchange('qty_requested')
    def _onchange_qty_requested_sync_box(self):
        for line in self:
            ratio = line.pcs_per_box or (line.product_id.pcs_per_box if line.product_id else 12) or 1
            if ratio > 0 and line.qty_requested:
                line.qty_box = round(line.qty_requested / ratio, 2)

    @api.onchange('product_id')
    def _onchange_product_id_sync_box(self):
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
