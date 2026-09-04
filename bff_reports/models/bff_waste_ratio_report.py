# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools

class BffWasteRatioReport(models.Model):
    _name = 'bff.waste.ratio.report'
    _description = 'Laporan Analytics Waste Ratio vs Sales Ratio'
    _auto = False
    _order = 'date desc'

    date = fields.Date(string='Tanggal / Periode', readonly=True)
    company_id = fields.Many2one('res.company', string='Cabang / Perusahaan', readonly=True)
    sales_revenue = fields.Float(string='Total Omset Penjualan (Rp)', readonly=True)
    spoilage_loss = fields.Float(string='Total Kerugian Spoilage/Defrosting (Rp)', readonly=True)
    waste_ratio = fields.Float(string='Rasio Kerugian (Waste Ratio %)', readonly=True, help='Persentase total kerugian barang rusak dibanding total omset penjualan.')

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                WITH sales_data AS (
                    SELECT 
                        DATE_TRUNC('month', date_order)::date AS date,
                        company_id,
                        SUM(amount_total) AS total_sales
                    FROM (
                        SELECT date_order, company_id, amount_total FROM pos_order WHERE state IN ('paid', 'done', 'invoiced')
                        UNION ALL
                        SELECT date_order, company_id, amount_total FROM sale_order WHERE state IN ('sale', 'done')
                    ) s_all
                    GROUP BY DATE_TRUNC('month', date_order)::date, company_id
                ),
                spoilage_data AS (
                    SELECT 
                        DATE_TRUNC('month', date)::date AS date,
                        company_id,
                        SUM(total_financial_loss) AS total_spoilage
                    FROM bff_spoilage_log
                    WHERE state = 'confirmed'
                    GROUP BY DATE_TRUNC('month', date)::date, company_id
                )
                SELECT 
                    ROW_NUMBER() OVER () AS id,
                    COALESCE(s.date, sp.date) AS date,
                    COALESCE(s.company_id, sp.company_id) AS company_id,
                    COALESCE(s.total_sales, 0.0) AS sales_revenue,
                    COALESCE(sp.total_spoilage, 0.0) AS spoilage_loss,
                    CASE 
                        WHEN COALESCE(s.total_sales, 0.0) > 0 THEN 
                            ROUND((COALESCE(sp.total_spoilage, 0.0) / s.total_sales * 100.0)::numeric, 2)
                        ELSE 0.0
                    END AS waste_ratio
                FROM sales_data s
                FULL OUTER JOIN spoilage_data sp ON s.date = sp.date AND s.company_id = sp.company_id
            )
        """ % self._table)
