# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BffStockOpname(models.Model):
    _name = 'bff.stock.opname'
    _description = 'Stok Opname Persediaan (Physical Inventory Count)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(
        string='Nomor Opname',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        tracking=True
    )
    date = fields.Date(
        string='Tanggal Opname',
        required=True,
        default=fields.Date.context_today
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Gudang',
        required=True
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Lokasi Gudang',
        required=True,
        domain="[('usage', '=', 'internal')]"
    )
    category_id = fields.Many2one(
        'product.category',
        string='Filter Kategori Produk'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Pembuat Dokumen',
        default=lambda self: self.env.user,
        required=True
    )
    counted_by_id = fields.Many2one(
        'res.users',
        string='Petugas Penghitung'
    )
    counted_at = fields.Datetime(
        string='Waktu Selesai Counting',
        readonly=True
    )
    validator_id = fields.Many2one(
        'res.users',
        string='Divalidasi Oleh',
        readonly=True,
        copy=False
    )
    date_validated = fields.Datetime(
        string='Waktu Validasi',
        readonly=True,
        copy=False
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Dalam Perhitungan'),
        ('validated', 'Divalidasi'),
        ('cancel', 'Dibatalkan')
    ], string='Status', default='draft', required=True, tracking=True)

    notes = fields.Text(
        string='Catatan / Keterangan Audit Opname'
    )
    line_ids = fields.One2many(
        'bff.stock.opname.line',
        'opname_id',
        string='Detail Produk Opname'
    )
    move_ids = fields.Many2many(
        'stock.move',
        string='Pergerakan Stok (Inventory Adjustment)',
        readonly=True,
        copy=False
    )
    move_count = fields.Integer(
        string='Jumlah Stock Move',
        compute='_compute_move_count'
    )
    product_count = fields.Integer(
        string='Jumlah Baris Produk',
        compute='_compute_summary',
        store=True
    )
    counted_product_count = fields.Integer(
        string='Baris Sudah Dihitung',
        compute='_compute_summary',
        store=True
    )
    total_difference_qty = fields.Float(
        string='Total Selisih Kuantitas',
        compute='_compute_summary',
        store=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Perusahaan',
        default=lambda self: self.env.company,
        required=True
    )

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id and self.warehouse_id.lot_stock_id:
            self.location_id = self.warehouse_id.lot_stock_id.id
        else:
            self.location_id = False

    @api.constrains('warehouse_id', 'location_id', 'company_id')
    def _check_warehouse_location_company(self):
        """
        Backend constraint: validate that:
        1. location_id is a child of warehouse_id.view_location_id
        2. company_id of document matches warehouse_id.company_id
        3. location_id.company_id matches document company_id
        """
        for rec in self:
            if not rec.warehouse_id or not rec.location_id:
                continue

            # Validate company consistency: document company vs warehouse company
            if rec.warehouse_id.company_id and rec.company_id != rec.warehouse_id.company_id:
                raise ValidationError(_(
                    "Perusahaan dokumen opname ('%s') tidak sesuai dengan perusahaan gudang '%s' ('%s'). "
                    "Harap sesuaikan Perusahaan atau Gudang."
                ) % (rec.company_id.name, rec.warehouse_id.name, rec.warehouse_id.company_id.name))

            # Validate location belongs to warehouse (child_of view_location_id)
            view_loc = rec.warehouse_id.view_location_id
            if view_loc:
                # search for the location within view_location_id hierarchy
                valid_loc = self.env['stock.location'].search([
                    ('id', '=', rec.location_id.id),
                    ('id', 'child_of', view_loc.id),
                    ('usage', '=', 'internal'),
                ], limit=1)
                if not valid_loc:
                    raise ValidationError(_(
                        "Lokasi '%s' bukan merupakan bagian dari gudang '%s'. "
                        "Lokasi harus merupakan lokasi internal di bawah gudang yang dipilih."
                    ) % (rec.location_id.display_name, rec.warehouse_id.name))

            # Validate location company vs document company
            if rec.location_id.company_id and rec.location_id.company_id != rec.company_id:
                raise ValidationError(_(
                    "Perusahaan lokasi '%s' ('%s') tidak sesuai dengan perusahaan dokumen opname ('%s')."
                ) % (rec.location_id.display_name, rec.location_id.company_id.name, rec.company_id.name))

    @api.depends('line_ids', 'line_ids.is_counted', 'line_ids.difference_qty')
    def _compute_summary(self):
        for rec in self:
            rec.product_count = len(rec.line_ids)
            rec.counted_product_count = len(rec.line_ids.filtered(lambda l: l.is_counted))
            rec.total_difference_qty = sum(rec.line_ids.filtered(lambda l: l.is_counted).mapped('difference_qty'))

    @api.depends('move_ids')
    def _compute_move_count(self):
        for rec in self:
            rec.move_count = len(rec.move_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('bff.stock.opname') or _('New')
        return super().create(vals_list)

    def action_populate_quants(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Pengambilan stok sistem hanya dapat dilakukan pada status Draft."))

        # Clear existing lines
        self.line_ids.unlink()

        domain = [('location_id', '=', self.location_id.id)]
        if self.category_id:
            domain.append(('product_id.categ_id', 'child_of', self.category_id.id))

        quants = self.env['stock.quant'].search(domain, order='product_id asc, lot_id asc')
        if not quants:
            raise UserError(_("Tidak ditemukan kuantitas stok di lokasi %s.") % self.location_id.display_name)

        line_vals = []
        for q in quants:
            line_vals.append((0, 0, {
                'quant_id': q.id,
                'product_id': q.product_id.id,
                'lot_id': q.lot_id.id if q.lot_id else False,
                'package_id': q.package_id.id if q.package_id else False,
                'owner_id': q.owner_id.id if q.owner_id else False,
                'system_qty': q.quantity,
                'physical_qty': False,
                'is_counted': False,
            }))

        self.write({'line_ids': line_vals})

    def action_start_counting(self):
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_("Belum ada baris produk pada dokumen opname ini. Klik 'Ambil Stok Sistem' terlebih dahulu."))
        self.state = 'in_progress'

    def action_set_physical_equals_system(self):
        self.ensure_one()
        if self.state not in ('draft', 'in_progress'):
            raise UserError(_("Fitur ini hanya dapat digunakan saat opname dalam status Draft atau Dalam Perhitungan."))
        uncounted = self.line_ids.filtered(lambda l: not l.is_counted)
        now = fields.Datetime.now()
        for line in uncounted:
            line.write({
                'physical_qty': line.system_qty,
                'is_counted': True,
                'counted_at': now,
            })

    def action_validate(self):
        self.ensure_one()
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise UserError(_("Hanya Manager Inventory yang berhak melakukan Validasi Stok Opname."))

        if self.state != 'in_progress':
            raise UserError(_("Hanya opname berstatus 'Dalam Perhitungan' yang dapat divalidasi."))

        # [FIX] Enforce full counting: reject if any line is still uncounted
        uncounted_lines = self.line_ids.filtered(lambda l: not l.is_counted)
        if uncounted_lines:
            raise UserError(_(
                "Validasi ditolak: Masih ada %d baris produk yang belum di-input stok fisiknya.\n"
                "Harap lengkapi seluruh perhitungan fisik sebelum melakukan validasi, atau gunakan "
                "'Set Stok Fisik = Stok Sistem' untuk produk yang stoknya sesuai."
            ) % len(uncounted_lines))

        counted_lines = self.line_ids.filtered(lambda l: l.is_counted)
        if not counted_lines:
            raise UserError(_("Belum ada produk yang di-input stok fisiknya."))

        now = fields.Datetime.now()

        # Strict validation of quant integrity before running adjustment
        quants_to_apply = self.env['stock.quant']
        for line in counted_lines:
            q = line.quant_id
            if not q or not q.exists():
                q = self.env['stock.quant'].search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', self.location_id.id),
                    ('lot_id', '=', line.lot_id.id if line.lot_id else False),
                    ('package_id', '=', line.package_id.id if line.package_id else False),
                    ('owner_id', '=', line.owner_id.id if line.owner_id else False),
                ], limit=1)
                if not q:
                    q = self.env['stock.quant'].create({
                        'product_id': line.product_id.id,
                        'location_id': self.location_id.id,
                        'lot_id': line.lot_id.id if line.lot_id else False,
                        'package_id': line.package_id.id if line.package_id else False,
                        'owner_id': line.owner_id.id if line.owner_id else False,
                        'quantity': 0.0,
                    })
                line.quant_id = q

            # Verify exact key match (product / location / lot / package / owner)
            if (q.product_id != line.product_id or
                q.location_id != self.location_id or
                q.lot_id != line.lot_id or
                q.package_id != line.package_id or
                q.owner_id != line.owner_id):
                raise UserError(_(
                    "Konflik Identitas Stok: Kombinasi produk/lot/lokasi pada baris '%s' sudah tidak sesuai dengan data quant Odoo. "
                    "Harap lakukan review opname."
                ) % line.product_id.display_name)

            # Apply user physical count to stock.quant native inventory_quantity
            q.inventory_quantity = line.physical_qty
            q.user_id = self.env.user.id
            quants_to_apply |= q

        # -----------------------------------------------------------------------
        # DETERMINISTIC STOCK MOVE TRACEABILITY
        #
        # Odoo 18 Trace:
        # _get_inventory_move_values() fills stock.move.name from context['inventory_name'].
        # No 'origin', 'reference', or 'group_id' is set on these moves.
        # The only unique identifier available is:
        #   - move.name == self.name  (from inventory_name context)
        #   - move.is_inventory == True
        #   - move.product_id in counted products
        #   - move.location_id / location_dest_id involves self.location_id
        #
        # Strategy: snapshot existing inventory-adjustment move IDs for this
        # location BEFORE applying, then capture only NEW moves at this location
        # whose name exactly matches our opname document number.
        # This is the most deterministic approach without patching Odoo core.
        # -----------------------------------------------------------------------
        existing_inv_move_ids_at_loc = set(self.env['stock.move'].search([
            ('is_inventory', '=', True),
            '|',
            ('location_id', '=', self.location_id.id),
            ('location_dest_id', '=', self.location_id.id),
        ]).ids)

        if quants_to_apply:
            # Pass inventory_name so Odoo sets move.name = self.name
            quants_to_apply.with_context(inventory_name=self.name).action_apply_inventory()

        # Capture only moves that:
        # 1. Are new (not in pre-existing snapshot)
        # 2. Are inventory adjustments
        # 3. Involve this location
        # 4. Have name matching this opname number (the most specific filter)
        created_moves = self.env['stock.move'].search([
            ('is_inventory', '=', True),
            ('name', 'ilike', self.name),
            '|',
            ('location_id', '=', self.location_id.id),
            ('location_dest_id', '=', self.location_id.id),
        ])
        # Secondary safety filter: only keep truly new moves
        created_moves = created_moves.filtered(lambda m: m.id not in existing_inv_move_ids_at_loc)

        self.write({
            'state': 'validated',
            'validator_id': self.env.user.id,
            'date_validated': now,
            'counted_at': self.counted_at or now,
            'counted_by_id': self.counted_by_id.id or self.env.user.id,
            'move_ids': [(6, 0, created_moves.ids)]
        })

    def action_cancel(self):
        self.ensure_one()
        if self.state == 'validated':
            raise UserError(_("Dokumen opname yang sudah Divalidasi tidak dapat dibatalkan langsung. Gunakan 'Set ke Draft' untuk membatalkan penyesuaian."))
        self.state = 'cancel'

    def action_reset_to_draft(self):
        self.ensure_one()
        if not self.env.user.has_group('stock.group_stock_manager'):
            raise UserError(_("Hanya Manager Inventory yang berhak mengembalikan dokumen Stok Opname ke Draft."))

        if self.state not in ('validated', 'in_progress', 'cancel'):
            raise UserError(_("Dokumen opname sudah berstatus Draft."))

        # If document was validated, revert stock quant back to original system_qty
        if self.state == 'validated':
            quants_to_revert = self.env['stock.quant']
            for line in self.line_ids.filtered(lambda l: l.is_counted):
                q = line.quant_id
                if not q or not q.exists():
                    q = self.env['stock.quant'].search([
                        ('product_id', '=', line.product_id.id),
                        ('location_id', '=', self.location_id.id),
                        ('lot_id', '=', line.lot_id.id if line.lot_id else False),
                        ('package_id', '=', line.package_id.id if line.package_id else False),
                        ('owner_id', '=', line.owner_id.id if line.owner_id else False),
                    ], limit=1)

                if q:
                    # Revert quant inventory quantity to line.system_qty
                    q.inventory_quantity = line.system_qty or 0.0
                    q.user_id = self.env.user.id
                    quants_to_revert |= q

            if quants_to_revert:
                quants_to_revert.with_context(inventory_name=_("Pembatalan Opname %s") % self.name).action_apply_inventory()

        self.write({
            'state': 'draft',
            'validator_id': False,
            'date_validated': False,
            'move_ids': [(5, 0, 0)],
        })
        self.message_post(body=_("Dokumen Stok Opname dikembalikan ke status Draft oleh %s.") % self.env.user.name)

    def action_view_moves(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_action")
        action['domain'] = [('id', 'in', self.move_ids.ids)]
        action['context'] = {'default_is_inventory': True}
        return action


class BffStockOpnameLine(models.Model):
    _name = 'bff.stock.opname.line'
    _description = 'Baris Detail Stok Opname'
    _order = 'opname_id desc, product_id asc, id asc'

    opname_id = fields.Many2one(
        'bff.stock.opname',
        string='Dokumen Opname',
        required=True,
        ondelete='cascade'
    )
    quant_id = fields.Many2one(
        'stock.quant',
        string='Ref Quant Technical',
        ondelete='set null'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Produk',
        required=True
    )
    product_code = fields.Char(
        string='Kode / SKU',
        related='product_id.default_code',
        store=True
    )
    category_id = fields.Many2one(
        'product.category',
        string='Kategori',
        related='product_id.categ_id',
        store=True
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot / Serial Number'
    )
    package_id = fields.Many2one(
        'stock.quant.package',
        string='Paket / Package'
    )
    owner_id = fields.Many2one(
        'res.partner',
        string='Pemilik / Owner'
    )
    # [FIX] company_id now follows the parent document's company, not user context
    company_id = fields.Many2one(
        'res.company',
        string='Perusahaan',
        related='opname_id.company_id',
        store=True,
        readonly=True,
    )
    system_qty = fields.Float(
        string='Stok Sistem',
        default=0.0,
        digits='Product Unit of Measure'
    )
    physical_qty = fields.Float(
        string='Stok Fisik',
        default=False,
        digits='Product Unit of Measure'
    )
    # is_counted is a plain stored Boolean, not computed.
    # Reason: Float fields always store 0.0 (never False) in PostgreSQL,
    # so we cannot distinguish 'uncounted' from 'counted with value 0'
    # using physical_qty value alone. Instead, is_counted is set explicitly
    # via write()/create() hooks when physical_qty is purposefully assigned.
    is_counted = fields.Boolean(
        string='Sudah Dihitung',
        default=False
    )
    difference_qty = fields.Float(
        string='Selisih',
        compute='_compute_difference',
        store=True,
        digits='Product Unit of Measure'
    )
    has_difference = fields.Boolean(
        string='Memiliki Selisih',
        compute='_compute_difference',
        store=True
    )
    product_uom_id = fields.Many2one(
        'uom.uom',
        string='Satuan',
        related='product_id.uom_id',
        readonly=True
    )
    counted_at = fields.Datetime(
        string='Waktu Hitung'
    )

    @api.model_create_multi
    def create(self, vals_list):
        """
        When physical_qty is explicitly provided during create (e.g. action_set_physical_equals_system),
        auto-set is_counted=True and counted_at unless the caller already set them.
        Lines created by action_populate_quants pass physical_qty=False which the ORM stores as 0.0,
        but they also explicitly pass is_counted=False, so the guard below won't trigger.
        """
        for vals in vals_list:
            # Only mark counted if is_counted was NOT explicitly set to False by the caller
            if vals.get('is_counted', None) is None and 'physical_qty' in vals:
                # physical_qty was supplied without an explicit is_counted flag
                vals.setdefault('is_counted', True)
                vals.setdefault('counted_at', fields.Datetime.now())
        return super().create(vals_list)

    def write(self, vals):
        """
        When physical_qty is written by user input, auto-set is_counted=True and counted_at.
        If the caller explicitly passes is_counted=False we respect that.
        """
        if 'physical_qty' in vals and 'is_counted' not in vals:
            vals['is_counted'] = True
            vals.setdefault('counted_at', fields.Datetime.now())
        return super().write(vals)

    @api.onchange('product_id', 'lot_id')
    def _onchange_product_id_lot_id(self):
        if not self.product_id:
            self.quant_id = False
            self.system_qty = 0.0
            return

        location = self.opname_id.location_id
        if not location:
            self.system_qty = 0.0
            return

        domain = [
            ('product_id', '=', self.product_id.id),
            ('location_id', '=', location.id),
        ]
        if self.lot_id:
            domain.append(('lot_id', '=', self.lot_id.id))
        else:
            domain.append(('lot_id', '=', False))

        quant = self.env['stock.quant'].search(domain, limit=1)
        if quant:
            self.quant_id = quant.id
            self.system_qty = quant.quantity
        else:
            self.quant_id = False
            self.system_qty = 0.0

    @api.onchange('physical_qty')
    def _onchange_physical_qty(self):
        if self.physical_qty is not False and self.physical_qty is not None:
            self.is_counted = True
            self.counted_at = fields.Datetime.now()

    @api.depends('physical_qty', 'system_qty', 'is_counted')
    def _compute_difference(self):
        for line in self:
            if line.is_counted:
                # Safe arithmetic: physical_qty=False/None treated as uncounted above,
                # so at this point physical_qty is always a valid float (including 0.0)
                phys = line.physical_qty if (line.physical_qty is not False and line.physical_qty is not None) else 0.0
                diff = phys - (line.system_qty or 0.0)
                line.difference_qty = diff
                rounding = (line.product_uom_id and line.product_uom_id.rounding) or 0.01
                line.has_difference = not fields.Float.is_zero(diff, precision_rounding=rounding)
            else:
                line.difference_qty = 0.0
                line.has_difference = False
