from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    bff_role = fields.Selection([
        ('cashier', 'Kasir (Point of Sale)'),
        ('warehouse', 'Orang / Staf Gudang (Inventory & Stock)'),
        ('manager', 'Manajer / Supervisor Operasional'),
    ], string='Role / Tugas Karyawan', default='cashier', help='Role operasional karyawan di Big Frozen Food')

    shift_schedule = fields.Selection([
        ('morning', 'Shift Pagi (07:30 - 15:30)'),
        ('afternoon', 'Shift Siang (13:00 - 21:00)'),
        ('full', 'Shift Full Time / Regular'),
    ], string='Jadwal Shift', default='morning')

    assigned_warehouse_id = fields.Many2one('stock.warehouse', string='Gudang Penugasan Utama')
    warehouse_responsibilities = fields.Text(
        string='Tugas Detail Gudang / Kasir',
        help='Detail tanggung jawab (contoh: mendata stock fisik, penerimaan barang supplier, penataan freezer, pencatatan expired date, dll.)'
    )

    commission_rate_percent = fields.Float(
        string='Rate Komisi Omset (%)',
        default=1.0,
        digits=(16, 2),
        help='Persentase komisi kasir dari total omset transaksi POS.'
    )

    clearance_bonus_percent = fields.Float(
        string='Bonus Produk Cuci Gudang (%)',
        default=5.0,
        digits=(16, 2),
        help='Persentase bonus ekstra dari omset produk Mendekati Expired / Cuci Gudang yang berhasil dijual.'
    )

    total_commission_earned = fields.Monetary(
        string='Total Komisi Diperoleh',
        compute='_compute_total_commission_earned',
        currency_field='currency_id'
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Mata Uang',
        default=lambda self: self.env.company.currency_id
    )

    def _compute_total_commission_earned(self):
        for emp in self:
            reports = self.env['cashier.commission.report'].search([
                ('employee_id', '=', emp.id),
                ('state', 'in', ['approved', 'paid'])
            ])
            emp.total_commission_earned = sum(reports.mapped('total_commission_payout'))

    @api.model_create_multi
    def create(self, vals_list):
        employees = super(HrEmployee, self).create(vals_list)
        for emp in employees:
            emp._sync_user_groups()
        return employees

    def write(self, vals):
        res = super(HrEmployee, self).write(vals)
        if 'bff_role' in vals or 'user_id' in vals:
            for emp in self:
                emp._sync_user_groups()
        return res

    def _sync_user_groups(self):
        """Menyinkronkan grup keamanan pengguna (res.users) berdasarkan role karyawan"""
        cashier_group = self.env.ref('bff_karyawan.group_bff_cashier', raise_if_not_found=False)
        warehouse_group = self.env.ref('bff_karyawan.group_bff_warehouse', raise_if_not_found=False)

        for emp in self:
            if not emp.user_id:
                continue
            user = emp.user_id
            if emp.bff_role == 'cashier':
                if cashier_group and cashier_group not in user.groups_id:
                    user.write({'groups_id': [(4, cashier_group.id)]})
            elif emp.bff_role == 'warehouse':
                if warehouse_group and warehouse_group not in user.groups_id:
                    user.write({'groups_id': [(4, warehouse_group.id)]})
