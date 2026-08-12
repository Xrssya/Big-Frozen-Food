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
