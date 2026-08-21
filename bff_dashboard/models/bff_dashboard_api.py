# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class BffDashboardApi(models.TransientModel):
    _name = 'bff.dashboard.api'
    _description = 'Big Frozen Food Executive Dashboard API'

    @api.model
    def get_dashboard_data(self, period='month'):
        """
        Fetch real-time aggregated metrics and chart data for Executive Dashboard.
        Periods: 'month' (Current Month), '30days' (Last 30 Days), 'year' (Year to Date), 'all' (All Time)
        """
        today = fields.Date.today()
        now = datetime.now()

        # Determine date filter boundaries
        if period == '30days':
            start_date = today - timedelta(days=30)
        elif period == 'year':
            start_date = date(today.year, 1, 1)
        elif period == 'all':
            start_date = date(2020, 1, 1)
        else:  # 'month' default
            start_date = date(today.year, today.month, 1)

        start_datetime = datetime.combine(start_date, datetime.min.time())

        # ----------------------------------------------------
        # 1. SALES DASHBOARD DATA
        # ----------------------------------------------------
        # B2B Sales Orders
        so_domain = [('state', 'in', ['sale', 'done']), ('date_order', '>=', start_datetime)]
        sale_orders = self.env['sale.order'].search(so_domain)
        total_so_revenue = sum(so.amount_total for so in sale_orders)

        # Retail POS Orders
        pos_domain = [('state', 'in', ['paid', 'done', 'invoiced']), ('date_order', '>=', start_datetime)]
        pos_orders = self.env['pos.order'].search(pos_domain)
        total_pos_revenue = sum(po.amount_total for po in pos_orders)

        total_sales_revenue = total_so_revenue + total_pos_revenue

        # Channel comparison: Agen / Reseller Sales Orders vs POS Toko
        channel_comparison = {
            'agen_sales': round(total_so_revenue, 2),
            'pos_sales': round(total_pos_revenue, 2),
        }

        # Daily Turnover (Last 14 Days)
        daily_labels = []
        daily_so_values = []
        daily_pos_values = []
        daily_total_values = []

        for i in range(13, -1, -1):
            d = today - timedelta(days=i)
            day_start = datetime.combine(d, datetime.min.time())
            day_end = datetime.combine(d, datetime.max.time())
            
            d_so = sum(so.amount_total for so in self.env['sale.order'].search([
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', day_start),
                ('date_order', '<=', day_end)
            ]))
            d_pos = sum(po.amount_total for po in self.env['pos.order'].search([
                ('state', 'in', ['paid', 'done', 'invoiced']),
                ('date_order', '>=', day_start),
                ('date_order', '<=', day_end)
            ]))
            
            daily_labels.append(d.strftime('%d %b'))
            daily_so_values.append(round(d_so, 2))
            daily_pos_values.append(round(d_pos, 2))
            daily_total_values.append(round(d_so + d_pos, 2))

        # Monthly Turnover (Last 6 Months)
        monthly_labels = []
        monthly_revenue_values = []

        for i in range(5, -1, -1):
            m_date = today - relativedelta(months=i)
            m_start = datetime(m_date.year, m_date.month, 1, 0, 0, 0)
            if m_date.month == 12:
                m_end = datetime(m_date.year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
            else:
                m_end = datetime(m_date.year, m_date.month + 1, 1, 0, 0, 0) - timedelta(seconds=1)

            m_so = sum(so.amount_total for so in self.env['sale.order'].search([
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', m_start),
                ('date_order', '<=', m_end)
            ]))
            m_pos = sum(po.amount_total for po in self.env['pos.order'].search([
                ('state', 'in', ['paid', 'done', 'invoiced']),
                ('date_order', '>=', m_start),
                ('date_order', '<=', m_end)
            ]))

            monthly_labels.append(m_date.strftime('%b %Y'))
            monthly_revenue_values.append(round(m_so + m_pos, 2))

        # Top 5 Best Selling Products
        product_totals = {}
        # Aggregate from sale.order.line
        so_lines = self.env['sale.order.line'].search([
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', start_datetime)
        ])
        for line in so_lines:
            pid = line.product_id.id
            if pid not in product_totals:
                product_totals[pid] = {
                    'id': pid,
                    'name': line.product_id.display_name,
                    'qty': 0.0,
                    'revenue': 0.0,
                    'uom': line.product_uom.name or 'pcs'
                }
            product_totals[pid]['qty'] += line.product_uom_qty
            product_totals[pid]['revenue'] += line.price_subtotal

        # Aggregate from pos.order.line
        pos_lines = self.env['pos.order.line'].search([
            ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
            ('order_id.date_order', '>=', start_datetime)
        ])
        for line in pos_lines:
            pid = line.product_id.id
            if pid not in product_totals:
                product_totals[pid] = {
                    'id': pid,
                    'name': line.product_id.display_name,
                    'qty': 0.0,
                    'revenue': 0.0,
                    'uom': line.product_uom_id.name or 'pcs'
                }
            product_totals[pid]['qty'] += line.qty
            product_totals[pid]['revenue'] += line.price_subtotal_incl

        sorted_products = sorted(product_totals.values(), key=lambda x: x['revenue'], reverse=True)[:5]
        top_5_products = [{
            'id': p['id'],
            'name': p['name'],
            'qty': round(p['qty'], 2),
            'revenue': round(p['revenue'], 2),
            'uom': p['uom']
        } for p in sorted_products]


        # ----------------------------------------------------
        # 2. STOCK & EXPIRY DASHBOARD DATA
        # ----------------------------------------------------
        # Internal Stock Quants
        quants = self.env['stock.quant'].search([
            ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0)
        ])
        
        total_stock_value = sum(q.quantity * (q.product_id.standard_price or q.product_id.list_price * 0.7) for q in quants)

        # Low Stock Calculation
        storable_products = self.env['product.product'].search([('is_storable', '=', True)])
        low_stock_list = []
        for p in storable_products:
            min_alert = getattr(p, 'min_stock_alert_qty', 10.0) or 10.0
            on_hand = p.qty_available
            if on_hand <= min_alert:
                low_stock_list.append({
                    'id': p.id,
                    'name': p.display_name,
                    'qty_available': round(on_hand, 2),
                    'min_alert_qty': round(min_alert, 2),
                    'uom': p.uom_id.name or 'pcs',
                })

        low_stock_count = len(low_stock_list)
        # Sort top 8 lowest stock for table view
        low_stock_items = sorted(low_stock_list, key=lambda x: x['qty_available'])[:8]

        # Near Expiry (FEFO) Calculation
        near_expiry_list = []
        near_expiry_count = 0
        expiry_threshold = today + timedelta(days=30)
        
        if 'use_date' in self.env['stock.lot']._fields or 'expiration_date' in self.env['stock.lot']._fields:
            lot_domain = [('expiration_date', '!=', False)] if 'expiration_date' in self.env['stock.lot']._fields else [('use_date', '!=', False)]
            lots = self.env['stock.lot'].search(lot_domain)
            for lot in lots:
                exp_dt = lot.expiration_date if hasattr(lot, 'expiration_date') and lot.expiration_date else getattr(lot, 'use_date', False)
                if exp_dt:
                    exp_date = exp_dt.date() if isinstance(exp_dt, datetime) else exp_dt
                    days_left = (exp_date - today).days
                    if days_left <= 30:
                        near_expiry_count += 1
                        status = 'EXPIRED' if days_left < 0 else ('CRITICAL' if days_left <= 14 else 'WARNING')
                        near_expiry_list.append({
                            'id': lot.id,
                            'product_name': lot.product_id.display_name,
                            'lot_name': lot.name,
                            'expiration_date': exp_date.strftime('%d %b %Y'),
                            'days_left': days_left,
                            'status': status,
                        })

        near_expiry_items = sorted(near_expiry_list, key=lambda x: x['days_left'])[:8]


        # ----------------------------------------------------
        # 3. PURCHASE DASHBOARD DATA
        # ----------------------------------------------------
        po_domain = [('state', 'in', ['purchase', 'done']), ('date_order', '>=', start_datetime)]
        purchase_orders = self.env['purchase.order'].search(po_domain)
        monthly_purchase_total = sum(po.amount_total for po in purchase_orders)

        supplier_spend = {}
        for po in purchase_orders:
            supp_name = po.partner_id.display_name
            if supp_name not in supplier_spend:
                supplier_spend[supp_name] = {'supplier': supp_name, 'po_count': 0, 'total': 0.0}
            supplier_spend[supp_name]['po_count'] += 1
            supplier_spend[supp_name]['total'] += po.amount_total

        sorted_suppliers = sorted(supplier_spend.values(), key=lambda x: x['total'], reverse=True)[:6]
        supplier_breakdown = [{
            'supplier': s['supplier'],
            'po_count': s['po_count'],
            'total': round(s['total'], 2)
        } for s in sorted_suppliers]


        return {
            'period': period,
            'sales': {
                'total_revenue': round(total_sales_revenue, 2),
                'so_revenue': round(total_so_revenue, 2),
                'pos_revenue': round(total_pos_revenue, 2),
                'channel_comparison': channel_comparison,
                'daily_labels': daily_labels,
                'daily_so': daily_so_values,
                'daily_pos': daily_pos_values,
                'daily_total': daily_total_values,
                'monthly_labels': monthly_labels,
                'monthly_revenue': monthly_revenue_values,
                'top_5_products': top_5_products,
            },
            'stock': {
                'total_valuation': round(total_stock_value, 2),
                'low_stock_count': low_stock_count,
                'low_stock_items': low_stock_items,
                'near_expiry_count': near_expiry_count,
                'near_expiry_items': near_expiry_items,
            },
            'purchase': {
                'monthly_total': round(monthly_purchase_total, 2),
                'supplier_breakdown': supplier_breakdown,
            }
        }
