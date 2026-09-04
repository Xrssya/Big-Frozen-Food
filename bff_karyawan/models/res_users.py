from odoo import models, fields, api

class ResUsers(models.Model):
    _inherit = 'res.users'

    bff_role = fields.Selection([
        ('kepala_toko', 'Kepala Toko'),
        ('asisten_kepala_toko', 'Asisten Kepala Toko'),
        ('kasir', 'Kasir'),
        ('kepala_gudang', 'Kepala Gudang'),
        ('staf_gudang', 'Staf Gudang'),
    ], string='Role Big Frozen Food', compute='_compute_bff_role', inverse='_inverse_bff_role', store=True)

    @api.depends('employee_ids.bff_role')
    def _compute_bff_role(self):
        for user in self:
            emp = user.employee_id
            if emp and emp.bff_role:
                user.bff_role = emp.bff_role
            else:
                user.bff_role = False

    def _inverse_bff_role(self):
        for user in self:
            if user.employee_id and user.bff_role:
                user.employee_id.bff_role = user.bff_role
                user.employee_id._sync_user_groups()
