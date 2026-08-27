# -*- coding: utf-8 -*-
from odoo import models, api
from datetime import date, datetime, timedelta


class BffDashboardApi(models.AbstractModel):
    _name = 'bff.dashboard.api'
    _description = 'Big Frozen Food Executive & Module Dashboard API'

    @api.model
    def get_dashboard_data(self, period='month', date_from=None, date_to=None, company_id=None):
        today = date.today()
        end_date = today

        # Determine date filter boundaries
        if period == 'custom' and date_from and date_to:
            try:
                start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            except Exception:
                start_date = date(today.year, today.month, 1)
                end_date = today
        elif period == '30days':
            start_date = today - timedelta(days=30)
        elif period == 'year':
            start_date = date(today.year, 1, 1)
        elif period == 'all':
            start_date = date(2020, 1, 1)
        else:  # 'month' default
            start_date = date(today.year, today.month, 1)

        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        company_domain = []
        if company_id and str(company_id).isdigit():
            company_domain = [('company_id', '=', int(company_id))]

        # ----------------------------------------------------
        # 1. SALES DASHBOARD DATA
        # ----------------------------------------------------
        # B2B Sales Orders
        so_domain = [
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', start_datetime),
            ('date_order', '<=', end_datetime)
        ] + company_domain
        sale_orders = self.env['sale.order'].search(so_domain)
        total_so_revenue = sum(so.amount_total for so in sale_orders)

        # Retail POS Orders
        pos_domain = [
            ('state', 'in', ['paid', 'done', 'invoiced']),
            ('date_order', '>=', start_datetime),
            ('date_order', '<=', end_datetime)
        ] + company_domain
        pos_orders = self.env['pos.order'].search(pos_domain)
        total_pos_revenue = sum(po.amount_total for po in pos_orders)

        total_sales_revenue = total_so_revenue + total_pos_revenue

        # Channel comparison: Agen / Reseller Sales Orders vs POS Toko
        channel_comparison = {
            'agen_sales': round(total_so_revenue, 2),
            'pos_sales': round(total_pos_revenue, 2),
        }

        # Daily Turnover Calculation
        daily_labels = []
        daily_dates = []
        daily_so_values = []
        daily_pos_values = []
        daily_total_values = []

        total_days = (end_date - start_date).days + 1
        if total_days > 31:
            # Step size to limit chart points to ~30 max
            step = max(1, total_days // 30)
            date_list = [start_date + timedelta(days=i) for i in range(0, total_days, step)]
        else:
            date_list = [start_date + timedelta(days=i) for i in range(total_days)]

        for d in date_list:
            d_start = datetime.combine(d, datetime.min.time())
            d_end = datetime.combine(d, datetime.max.time())

            d_so = sum(so.amount_total for so in self.env['sale.order'].search([
                ('state', 'in', ['sale', 'done']),
                ('date_order', '>=', d_start),
                ('date_order', '<=', d_end)
            ]))
            d_pos = sum(po.amount_total for po in self.env['pos.order'].search([
                ('state', 'in', ['paid', 'done', 'invoiced']),
                ('date_order', '>=', d_start),
                ('date_order', '<=', d_end)
            ]))

            daily_labels.append(d.strftime('%d %b'))
            daily_dates.append(d.strftime('%Y-%m-%d'))
            daily_so_values.append(round(d_so, 2))
            daily_pos_values.append(round(d_pos, 2))
            daily_total_values.append(round(d_so + d_pos, 2))

        # Monthly Turnover
        monthly_labels = []
        monthly_info = []
        monthly_revenue_values = []
        current_year = today.year
        for m in range(1, 13):
            if m > today.month and period != 'year' and period != 'all':
                break
            m_start = datetime(current_year, m, 1, 0, 0, 0)
            if m == 12:
                m_end = datetime(current_year, 12, 31, 23, 59, 59)
            else:
                next_month = datetime(current_year, m + 1, 1, 0, 0, 0)
                m_end = next_month - timedelta(seconds=1)

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

            monthly_labels.append(m_start.strftime('%b %Y'))
            monthly_info.append({
                'start': m_start.strftime('%Y-%m-%d 00:00:00'),
                'end': m_end.strftime('%Y-%m-%d 23:59:59'),
                'label': m_start.strftime('%b %Y')
            })
            monthly_revenue_values.append(round(m_so + m_pos, 2))

        # Top 5 Best Selling Products
        product_totals = {}
        so_lines = self.env['sale.order.line'].search([
            ('order_id.state', 'in', ['sale', 'done']),
            ('order_id.date_order', '>=', start_datetime),
            ('order_id.date_order', '<=', end_datetime)
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

        pos_lines = self.env['pos.order.line'].search([
            ('order_id.state', 'in', ['paid', 'done', 'invoiced']),
            ('order_id.date_order', '>=', start_datetime),
            ('order_id.date_order', '<=', end_datetime)
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
        quants = self.env['stock.quant'].search([
            ('location_id.usage', '=', 'internal'),
            ('quantity', '>', 0)
        ])
        total_stock_value = sum(q.quantity * (q.product_id.standard_price or q.product_id.list_price * 0.7) for q in quants)

        if 'is_storable' in self.env['product.product']._fields:
            storable_products = self.env['product.product'].search([('is_storable', '=', True)])
        else:
            storable_products = self.env['product.product'].search([('type', '=', 'consu')])
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
        low_stock_items = sorted(low_stock_list, key=lambda x: x['qty_available'])[:8]

        near_expiry_list = []
        near_expiry_count = 0
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
        po_domain = [
            ('state', 'in', ['purchase', 'done']),
            ('date_order', '>=', start_datetime),
            ('date_order', '<=', end_datetime)
        ]
        purchase_orders = self.env['purchase.order'].search(po_domain)
        monthly_purchase_total = sum(po.amount_total for po in purchase_orders)

        supplier_spend = {}
        for po in purchase_orders:
            supp_id = po.partner_id.id
            supp_name = po.partner_id.display_name
            if supp_id not in supplier_spend:
                supplier_spend[supp_id] = {'partner_id': supp_id, 'supplier': supp_name, 'po_count': 0, 'total': 0.0}
            supplier_spend[supp_id]['po_count'] += 1
            supplier_spend[supp_id]['total'] += po.amount_total

        sorted_suppliers = sorted(supplier_spend.values(), key=lambda x: x['total'], reverse=True)[:6]
        supplier_breakdown = [{
            'partner_id': s['partner_id'],
            'supplier': s['supplier'],
            'po_count': s['po_count'],
            'total': round(s['total'], 2)
        } for s in sorted_suppliers]

        # ----------------------------------------------------
        # 4. POS RETAIL DASHBOARD SPECIFIC DATA
        # ----------------------------------------------------
        pos_orders_count = len(pos_orders)
        avg_basket_size = (total_pos_revenue / pos_orders_count) if pos_orders_count > 0 else 0.0

        active_sessions = self.env['pos.session'].search([('state', '=', 'opened')])
        session_list = [{
            'id': s.id,
            'name': s.name,
            'config_name': s.config_id.name,
            'user_name': s.user_id.name,
            'start_at': s.start_at.strftime('%d %b %H:%M') if s.start_at else '-',
        } for s in active_sessions]

        pos_product_totals = {}
        for line in pos_lines:
            pid = line.product_id.id
            if pid not in pos_product_totals:
                pos_product_totals[pid] = {
                    'id': pid,
                    'name': line.product_id.display_name,
                    'qty': 0.0,
                    'revenue': 0.0,
                    'uom': line.product_uom_id.name or 'pcs'
                }
            pos_product_totals[pid]['qty'] += line.qty
            pos_product_totals[pid]['revenue'] += line.price_subtotal_incl

        sorted_pos_prods = sorted(pos_product_totals.values(), key=lambda x: x['revenue'], reverse=True)[:5]
        top_5_pos_products = [{
            'id': p['id'],
            'name': p['name'],
            'qty': round(p['qty'], 2),
            'revenue': round(p['revenue'], 2),
            'uom': p['uom']
        } for p in sorted_pos_prods]

        return {
            'period': period,
            'date_from': start_date.strftime('%Y-%m-%d'),
            'date_to': end_date.strftime('%Y-%m-%d'),
            'sales': {
                'total_revenue': round(total_sales_revenue, 2),
                'so_revenue': round(total_so_revenue, 2),
                'pos_revenue': round(total_pos_revenue, 2),
                'so_ids': sale_orders.ids,
                'pos_ids': pos_orders.ids,
                'channel_comparison': channel_comparison,
                'daily_labels': daily_labels,
                'daily_dates': daily_dates,
                'daily_so': daily_so_values,
                'daily_pos': daily_pos_values,
                'daily_total': daily_total_values,
                'monthly_labels': monthly_labels,
                'monthly_info': monthly_info,
                'monthly_revenue': monthly_revenue_values,
                'top_5_products': top_5_products,
            },
            'stock': {
                'total_valuation': round(total_stock_value, 2),
                'low_stock_count': low_stock_count,
                'low_stock_items': low_stock_items,
                'low_stock_ids': [p['id'] for p in low_stock_list],
                'near_expiry_count': near_expiry_count,
                'near_expiry_items': near_expiry_items,
                'near_expiry_ids': [lot['id'] for lot in near_expiry_list],
            },
            'purchase': {
                'monthly_total': round(monthly_purchase_total, 2),
                'supplier_breakdown': supplier_breakdown,
                'po_ids': purchase_orders.ids,
            },
            'pos': {
                'total_revenue': round(total_pos_revenue, 2),
                'orders_count': pos_orders_count,
                'avg_basket_size': round(avg_basket_size, 2),
                'active_sessions_count': len(active_sessions),
                'session_list': session_list,
                'top_5_products': top_5_pos_products,
                'daily_labels': daily_labels,
                'daily_dates': daily_dates,
                'daily_values': daily_pos_values,
            }
        }

    @api.model
    def get_popular_times_data(self, company_id=None, day_of_week=None):
        """Calculates Popular Times (Jam Ramai) & Quiet Days Analytics (Analisis Hari Sepi Cabang)"""
        branches = self.env['res.company'].search([('name', 'ilike', 'Big Frozen Food')])
        branch_list = [{'id': b.id, 'name': b.name} for b in branches]

        domain = [('state', 'in', ['paid', 'done', 'invoiced'])]
        if company_id and str(company_id).isdigit() and int(company_id) > 0:
            target_company_id = int(company_id)
            domain.append(('company_id', '=', target_company_id))
            target_comp = self.env['res.company'].browse(target_company_id)
            target_company_name = target_comp.name if target_comp.exists() else "Semua Cabang Toko"
        else:
            target_company_name = "Semua Cabang Toko"

        cutoff_date = datetime.now() - timedelta(days=60)
        domain.append(('date_order', '>=', cutoff_date))
        orders = self.env['pos.order'].search(domain)

        day_names_id = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']

        day_counts = {d: {h: 0 for h in range(24)} for d in range(7)}
        day_totals = {d: 0 for d in range(7)}

        for ord_rec in orders:
            if not ord_rec.date_order:
                continue
            dt = ord_rec.date_order
            d_idx = dt.weekday()
            hr = dt.hour
            day_counts[d_idx][hr] += 1
            day_totals[d_idx] += 1

        num_weeks = max(1.0, 60.0 / 7.0)
        daily_averages = {}
        for d in range(7):
            avg_o = day_totals[d] / num_weeks
            daily_averages[d] = round(avg_o, 1)

        sorted_days = sorted(daily_averages.items(), key=lambda x: x[1])
        quietest_day_idx, quietest_avg = sorted_days[0]
        busiest_day_idx, busiest_avg = sorted_days[-1]

        overall_avg = (sum(daily_averages.values()) / 7.0) or 1.0
        quietest_pct = round((quietest_avg / overall_avg) * 100, 1) if overall_avg > 0 else 0.0
        busiest_pct = round((busiest_avg / overall_avg) * 100, 1) if overall_avg > 0 else 0.0

        quietest_day_info = {
            'day_name': day_names_id[quietest_day_idx],
            'avg_orders': quietest_avg,
            'percentage': quietest_pct
        }
        busiest_day_info = {
            'day_name': day_names_id[busiest_day_idx],
            'avg_orders': busiest_avg,
            'percentage': busiest_pct
        }

        if day_of_week is not None and str(day_of_week).isdigit():
            selected_day_idx = int(day_of_week) % 7
        else:
            selected_day_idx = quietest_day_idx

        current_day_name = day_names_id[selected_day_idx]
        hourly_raw = day_counts[selected_day_idx]

        max_hour_count = max([hourly_raw[h] for h in range(6, 23)] or [1])
        if max_hour_count == 0:
            max_hour_count = 1

        peak_hour = 12
        max_h_cnt = -1

        hourly_data = []
        for h in range(6, 23):
            cnt = hourly_raw[h]
            pct = round((cnt / float(max_hour_count)) * 100, 1)
            if cnt > max_h_cnt:
                max_h_cnt = cnt
                peak_hour = h

            hourly_data.append({
                'hour': h,
                'label': f"{h:02d}",
                'count': cnt,
                'percentage': pct
            })

        peak_hours_label = f"{peak_hour:02d}:00 - {(peak_hour+2):02d}:00 WIB"

        day_avg = daily_averages[selected_day_idx]
        if day_avg <= quietest_avg * 1.25:
            status_level = "quiet"
            status_badge = "🔴 HARI SANGAT SEPI"
            status_pill_text = f"Tidak ramai — hanya {day_avg} transaksi/hari ({quietest_pct}% dari normal)"
            status_desc = "Tingkat kunjungan & transaksi sangat sepi"
            option_a = f"Menetapkan hari {current_day_name} sebagai HARI LIBUR OPERASIONAL CABANG untuk efisiensi listrik freezer & biaya operasional."
            option_b = f"Pengurangan shift kasir (cukup 1 kasir part-time) & selenggarakan promo Flash Sale khusus hari {current_day_name}."
            recommendation = (
                f"Berdasarkan analisis historis 60 hari terakhir, cabang {target_company_name} "
                f"pada hari {current_day_name} memiliki tingkat transaksi paling sepi "
                f"(rata-rata {day_avg} transaksi/hari, atau {quietest_pct}% dari rata-rata normal)."
            )
        elif day_avg >= busiest_avg * 0.75:
            status_level = "busy"
            status_badge = "🟢 HARI SANGAT RAMAI"
            status_pill_text = f"Sangat ramai — rata-rata {day_avg} transaksi/hari ({busiest_pct}% dari normal)"
            status_desc = "Tingkat kunjungan & transaksi sangat padat"
            option_a = f"Pastikan seluruh freezer terisi penuh (full restock H-1 sebelum hari {current_day_name})."
            option_b = f"Buka seluruh lane kasir POS & siapkan staf tambahan untuk mengurai antrean pelanggan pada jam puncak ({peak_hours_label})."
            recommendation = (
                f"Berdasarkan analisis historis, cabang {target_company_name} pada hari {current_day_name} "
                f"mencapai puncak keramaian (rata-rata {day_avg} transaksi/hari, jam puncak {peak_hours_label})."
            )
        else:
            status_level = "normal"
            status_badge = "🟡 TIDAK TERLALU RAMAI"
            status_pill_text = f"Tingkat keramaian sedang — rata-rata {day_avg} transaksi/hari"
            status_desc = "Tingkat kunjungan & transaksi stabil/sedang"
            option_a = f"Pertahankan alokasi shift kasir & persediaan stok saat ini karena sudah berada pada kondisi optimal."
            option_b = f"Monitor stok produk fast-moving agar kestabilan penjualan tetap terjaga."
            recommendation = (
                f"Cabang {target_company_name} pada hari {current_day_name} berada pada kondisi operasional normal "
                f"(rata-rata {day_avg} transaksi/hari)."
            )

        return {
            'branches': branch_list,
            'selected_branch_id': company_id or 'all',
            'selected_branch_name': target_company_name,
            'selected_day_idx': selected_day_idx,
            'selected_day_name': current_day_name,
            'days_list': [{'idx': i, 'name': day_names_id[i]} for i in range(7)],
            'hourly_data': hourly_data,
            'daily_averages': [{'day_name': day_names_id[i], 'avg': daily_averages[i]} for i in range(7)],
            'quietest_day': quietest_day_info,
            'busiest_day': busiest_day_info,
            'peak_hours_label': peak_hours_label,
            'status_level': status_level,
            'status_badge': status_badge,
            'status_pill_text': status_pill_text,
            'status_desc': status_desc,
            'option_a': option_a,
            'option_b': option_b,
            'owner_recommendation': recommendation,
        }
