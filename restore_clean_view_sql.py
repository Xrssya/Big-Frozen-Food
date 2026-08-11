#!/usr/bin/env python3
import sys

sys.path.insert(0, '/home/setyo/developer/odoo18')
import odoo
from odoo import api, SUPERUSER_ID

DB_NAME = 'big_frozen_food'

def run():
    odoo.tools.config.parse_config(['-c', '/home/setyo/developer/odoo/odoo-BigFrozenFood/big_frozen_food.conf', '-d', DB_NAME])
    registry = odoo.registry(DB_NAME)
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        print("=== RESTORING CLEAN INVOICE VIEW VIA BASE XML ===")

        inv_view = env.ref('account.report_invoice_document')

        # Clean standard arch for account.report_invoice_document
        clean_arch = """<t t-name="account.report_invoice_document">
            <t t-call="web.external_layout">
                <t t-set="o" t-value="o.with_context(lang=lang)"/>
                <t t-set="forced_vat" t-value="o.fiscal_position_id.foreign_vat"/>
                <div class="row">
                    <t t-if="o.partner_shipping_id and (o.partner_shipping_id != o.partner_id)">
                        <div class="col-6">
                            <t t-set="information_block">
                                <div data-field="partner_shipping_id" t-field="o.partner_shipping_id" t-options='{"widget": "contact", "fields": ["address", "name"], "no_marker": True}'/>
                            </t>
                        </div>
                    </t>
                </div>
                <div class="mt-5 clear-both">
                    <div class="page mb-4">
                        <h2>
                            <span t-if="not o.name or o.name == '/'">Unposted Invoice</span>
                            <span t-else="" t-field="o.name"/>
                        </h2>
                        <div class="row mt-4 mb-4" id="informations">
                            <div class="col" t-if="o.invoice_date" name="invoice_date">
                                <strong>Tanggal Faktur:</strong>
                                <p class="m-0" t-field="o.invoice_date"/>
                            </div>
                            <div class="col" t-if="o.invoice_date_due and o.move_type == 'out_invoice' and o.state == 'posted'" name="due_date">
                                <strong>Tanggal Jatuh Tempo:</strong>
                                <p class="m-0" t-field="o.invoice_date_due"/>
                            </div>
                            <div class="col" t-if="o.delivery_date" name="delivery_date">
                                <strong>Tanggal Pengiriman:</strong>
                                <p class="m-0" t-field="o.delivery_date"/>
                            </div>
                            <div class="col" t-if="o.invoice_origin" name="origin">
                                <strong>Sumber:</strong>
                                <p class="m-0" t-field="o.invoice_origin"/>
                            </div>
                            <div class="col" t-if="o.ref" name="reference">
                                <strong>Referensi:</strong>
                                <p class="m-0" t-field="o.ref"/>
                            </div>
                        </div>
                        <t t-set="display_discount" t-value="any(l.discount for l in o.invoice_line_ids)"/>
                        <div class="oe_structure"/>
                        <table class="table table-sm o_main_table table-borderless" name="invoice_line_table">
                            <thead>
                                <tr>
                                    <th name="th_description" class="text-start"><span>Deskripsi</span></th>
                                    <th name="th_quantity" class="text-end"><span>Jumlah</span></th>
                                    <th name="th_priceunit" class="text-end"><span>Harga Satuan</span></th>
                                    <th name="th_taxes" class="text-end"><span>Pajak</span></th>
                                    <th name="th_subtotal" class="text-end"><span>Nominal</span></th>
                                </tr>
                            </thead>
                            <tbody class="invoice_tbody">
                                <t t-set="current_subtotal" t-value="0"/>
                                <t t-set="lines" t-value="o.invoice_line_ids.sorted(key=lambda l: (-l.sequence, l.date, l.id))"/>
                                <t t-foreach="lines" t-as="line">
                                    <t t-set="current_subtotal" t-value="current_subtotal + line.price_subtotal"/>
                                    <tr>
                                        <td name="account_invoice_line_name"><span t-field="line.name" t-options="{'widget': 'text'}"/></td>
                                        <td class="text-end"><span t-field="line.quantity"/></td>
                                        <td class="text-end"><span t-field="line.price_unit"/></td>
                                        <td class="text-end"><span t-esc="', '.join(map(lambda x: (x.name or ''), line.tax_ids))"/></td>
                                        <td class="text-end o_price_total"><span t-field="line.price_subtotal"/></td>
                                    </tr>
                                </t>
                            </tbody>
                        </table>
                        <div class="clearfix mb-4">
                            <div id="total" class="row">
                                <div class="col-6 str-col">
                                    <p t-if="o.payment_reference" name="payment_communication">
                                        Komunikasi Pembayaran: <b><span t-field="o.payment_reference"/></b>
                                    </p>
                                </div>
                                <div class="col-6 str-col ms-auto">
                                    <table class="table table-sm table-borderless" style="page-break-inside: avoid;">
                                        <tr class="border-black o_subtotal" style="">
                                            <td><strong>Jumlah Sebelum Pajak</strong></td>
                                            <td class="text-end"><span t-field="o.amount_untaxed"/></td>
                                        </tr>
                                        <tr t-foreach="o.amount_by_group" t-as="amount_by_group">
                                            <td><span t-esc="amount_by_group[0]"/></td>
                                            <td class="text-end o_price_total"><span t-esc="amount_by_group[1]"/></td>
                                        </tr>
                                        <tr class="border-black o_total">
                                            <td><strong>Total</strong></td>
                                            <td class="text-end"><span t-field="o.amount_total"/></td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </t>
        </t>"""

        cr.execute("UPDATE ir_ui_view SET arch_db = %s WHERE id = %s", (f"<data>{clean_arch}</data>", inv_view.id))
        print(" Updated arch_db in SQL directly.")

        # Test rendering PDF for INV/2026/00018
        inv = env['account.move'].search([('name', '=', 'INV/2026/00018')], limit=1)
        report = env.ref('account.account_invoices')
        pdf_content, _ = report._render_qweb_pdf(report.id, [inv.id])
        
        pdf_path = '/home/setyo/Downloads/CLEAN_HEADER_INV_00018.pdf'
        with open(pdf_path, 'wb') as f:
            f.write(pdf_content)
        print(f" Generated clean PDF at {pdf_path}")

        cr.commit()
        print("=== SUCCESS: CLEAN SINGLE GLOBAL HEADER RESTORED ===")

if __name__ == '__main__':
    run()
