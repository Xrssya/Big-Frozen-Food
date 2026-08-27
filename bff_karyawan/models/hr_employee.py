from odoo import models, fields, api

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    ROLE_LABEL_MAP = {
        'kepala_toko': 'Kepala Toko',
        'asisten_kepala_toko': 'Asisten Kepala Toko',
        'kasir': 'Kasir',
        'kepala_gudang': 'Kepala Gudang',
    }

    bff_role = fields.Selection([
        ('kepala_toko', 'Kepala Toko'),
        ('asisten_kepala_toko', 'Asisten Kepala Toko'),
        ('kasir', 'Kasir'),
        ('kepala_gudang', 'Kepala Gudang'),
    ], string='Role / Tugas Karyawan', default='kasir', help='Role operasional karyawan di Big Frozen Food')

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

    @api.onchange('bff_role')
    def _onchange_bff_role_set_tags(self):
        """Otomatis memasang Label (Category ID) sesuai dengan role yang dipilih"""
        if self.bff_role in self.ROLE_LABEL_MAP:
            target_label_name = self.ROLE_LABEL_MAP[self.bff_role]
            all_role_names = set(self.ROLE_LABEL_MAP.values())
            
            tag = self.env['hr.employee.category'].search([('name', '=', target_label_name)], limit=1)
            if not tag:
                tag = self.env['hr.employee.category'].create({'name': target_label_name})
            
            existing_tags = self.category_ids.filtered(lambda c: c.name not in all_role_names)
            self.category_ids = [(6, 0, (existing_tags | tag).ids)]

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
        """Menyinkronkan grup keamanan pengguna (res.users) dan Label Tag berdasarkan role karyawan"""
        g_kepala_toko = self.env.ref('bff_karyawan.group_bff_kepala_toko', raise_if_not_found=False)
        g_asisten_kepala_toko = self.env.ref('bff_karyawan.group_bff_asisten_kepala_toko', raise_if_not_found=False)
        g_cashier = self.env.ref('bff_karyawan.group_bff_cashier', raise_if_not_found=False)
        g_gudang = self.env.ref('bff_karyawan.group_bff_kepala_gudang', raise_if_not_found=False)

        all_role_names = set(self.ROLE_LABEL_MAP.values())

        for emp in self:
            role = emp.bff_role
            if role in self.ROLE_LABEL_MAP:
                target_label_name = self.ROLE_LABEL_MAP[role]

                # 1. Sync Employee Label Tag (hr.employee.category)
                emp_tag = self.env['hr.employee.category'].search([('name', '=', target_label_name)], limit=1)
                if not emp_tag:
                    emp_tag = self.env['hr.employee.category'].create({'name': target_label_name})
                
                other_tags = emp.category_ids.filtered(lambda c: c.name not in all_role_names)
                new_emp_tags = (other_tags | emp_tag).ids
                if set(emp.category_ids.ids) != set(new_emp_tags):
                    emp.write({'category_ids': [(6, 0, new_emp_tags)]})

                # 2. Sync User & Partner Permissions & Tags
                if emp.user_id:
                    user = emp.user_id
                    all_groups = [g for g in [g_kepala_toko, g_asisten_kepala_toko, g_cashier, g_gudang] if g]
                    target_group = None
                    if role == 'kepala_toko':
                        target_group = g_kepala_toko
                    elif role == 'asisten_kepala_toko':
                        target_group = g_asisten_kepala_toko
                    elif role == 'kasir':
                        target_group = g_cashier
                    elif role == 'kepala_gudang':
                        target_group = g_gudang

                    group_cmds = []
                    for g in all_groups:
                        if target_group and g.id == target_group.id:
                            if g.id not in user.groups_id.ids:
                                group_cmds.append((4, g.id))
                        else:
                            if g.id in user.groups_id.ids:
                                group_cmds.append((3, g.id))
                    if group_cmds:
                        user.write({'groups_id': group_cmds})

                    # Sync Partner Contact Label (res.partner.category)
                    if user.partner_id:
                        p_tag = self.env['res.partner.category'].search([('name', '=', target_label_name)], limit=1)
                        if not p_tag:
                            p_tag = self.env['res.partner.category'].create({'name': target_label_name})
                        
                        other_p_tags = user.partner_id.category_id.filtered(lambda c: c.name not in all_role_names)
                        new_p_tags = (other_p_tags | p_tag).ids
                        if set(user.partner_id.category_id.ids) != set(new_p_tags):
                            user.partner_id.write({'category_id': [(6, 0, new_p_tags)]})
