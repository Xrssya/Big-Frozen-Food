# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class BffSpoilageLog(models.Model):
    _name = 'bff.spoilage.log'
    _description = 'Pencatatan Barang Rusak / Lumer (Spoilage & Defrosting Log)'
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Nomor Referensi',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Baru')
    )
    date = fields.Datetime(
        string='Tanggal Kejadian',
        required=True,
        default=fields.Datetime.now,
    )
    user_id = fields.Many2one(
        'res.users',
        string='Pelapor / Penanggung Jawab',
        required=True,
        default=lambda self: self.env.user,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Cabang / Perusahaan',
        required=True,
        default=lambda self: self.env.company,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Lokasi Gudang / Freezer Origin',
        required=True,
        domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
    )
    reason_code = fields.Selection([
        ('defrost_power', '⚡ Listrik Padam / Mesin Freezer Mati'),
        ('defrost_door', '🚪 Pintu Freezer Terbuka / Suhu Naik'),
        ('packaging_damaged', '📦 Kemasan Bocor / Damaged Packaging'),
        ('expired', '⏳ Kadaluarsa / Past Expiry Date'),
        ('quality_decay', '🧪 Penurunan Kualitas / Berbau'),
        ('other', '📝 Lain-lain')
    ], string='Alasan Kerusakan', required=True, default='defrost_power')

    notes = fields.Text(string='Catatan / Kronologi Kejadian')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Disetujui & Potong Stok'),
        ('cancel', 'Dibatalkan')
    ], string='Status', default='draft', required=True, tracking=True)

    line_ids = fields.One2many(
        'bff.spoilage.log.line',
        'spoilage_id',
        string='Daftar Barang Rusak / Lumer',
    )
    total_financial_loss = fields.Float(
        string='Total Kerugian Finansial (HPP)',
        compute='_compute_total_financial_loss',
        store=True,
        help='Total estimasi kerugian dalam Rupiah berdasarkan HPP / Standard Cost produk.'
    )
    scrap_ids = fields.One2many('stock.scrap', 'spoilage_log_id', string='Dokumen Scrap Stok')
    scrap_count = fields.Integer(string='Jumlah Scrap', compute='_compute_scrap_count')

    @api.depends('line_ids.total_loss')
    def _compute_total_financial_loss(self):
        for rec in self:
            rec.total_financial_loss = sum(line.total_loss for line in rec.line_ids)

    @api.depends('scrap_ids')
    def _compute_scrap_count(self):
        for rec in self:
            rec.scrap_count = len(rec.scrap_ids)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Baru')) == _('Baru'):
                vals['name'] = self.env['ir.sequence'].next_by_code('bff.spoilage.log') or _('Baru')
        return super(BffSpoilageLog, self).create(vals_list)

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Harap tambahkan setidaknya satu produk barang rusak/lumer!'))

            scrap_obj = self.env['stock.scrap']
            for line in rec.line_ids:
                if line.qty <= 0:
                    raise UserError(_('Kuantitas barang rusak untuk produk %s harus lebih dari 0!') % line.product_id.display_name)

                scrap_vals = {
                    'product_id': line.product_id.id,
                    'scrap_qty': line.qty,
                    'product_uom_id': line.uom_id.id or line.product_id.uom_id.id,
                    'location_id': rec.location_id.id,
                    'lot_id': line.lot_id.id if line.lot_id else False,
                    'company_id': rec.company_id.id,
                    'origin': rec.name,
                    'spoilage_log_id': rec.id,
                }
                scrap = scrap_obj.create(scrap_vals)
                scrap.action_validate_scrap()

            rec.state = 'confirmed'

    def action_cancel(self):
        for rec in self:
            if rec.state == 'confirmed':
                raise UserError(_('Dokumen yang sudah disetujui & dipotong stok tidak dapat dibatalkan!'))
            rec.state = 'cancel'

    def action_draft(self):
        for rec in self:
            if rec.state == 'confirmed':
                raise UserError(_('Dokumen yang sudah disetujui tidak dapat dikembalikan ke draft!'))
            rec.state = 'draft'

    def action_view_scraps(self):
        self.ensure_one()
        return {
            'name': _('Penyesuaian Scrap Stok'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.scrap',
            'view_mode': 'list,form',
            'domain': [('spoilage_log_id', '=', self.id)],
        }


class BffSpoilageLogLine(models.Model):
    _name = 'bff.spoilage.log.line'
    _description = 'Detail Baris Barang Rusak / Lumer'

    spoilage_id = fields.Many2one('bff.spoilage.log', string='Ref Spoilage Log', ondelete='cascade', required=True)
    product_id = fields.Many2one('product.product', string='Produk', required=True, domain="[('type', '=', 'product')]")
    lot_id = fields.Many2one('stock.lot', string='Lot / Batch Number', domain="[('product_id', '=', product_id)]")
    qty = fields.Float(string='Jumlah Rusak (Qty)', required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Satuan (UoM)', related='product_id.uom_id', store=True, readonly=True)
    cost_price = fields.Float(string='HPP Satuan (Rp)', compute='_compute_cost_price', store=True, readonly=False)
    total_loss = fields.Float(string='Subtotal Kerugian (Rp)', compute='_compute_total_loss', store=True)

    @api.depends('product_id')
    def _compute_cost_price(self):
        for line in self:
            if line.product_id:
                line.cost_price = line.product_id.standard_price or 0.0
            else:
                line.cost_price = 0.0

    @api.depends('qty', 'cost_price')
    def _compute_total_loss(self):
        for line in self:
            line.total_loss = line.qty * line.cost_price


class StockScrapSpoilage(models.Model):
    _inherit = 'stock.scrap'

    spoilage_log_id = fields.Many2one('bff.spoilage.log', string='Spoilage Log Ref', readonly=True)
