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
        print("=== APPLYING BULLETPROOF INDONESIAN STANDARD SALES INVOICE TEMPLATE ===")

        # 1. Update Tax ID 1 to PPN 11%
        tax_11 = env['account.tax'].browse(1)
        tax_11.write({'name': 'PPN 11%', 'amount': 11.0, 'description': 'PPN 11%'})

        # 2. Update tax groups
        for tg in env['account.tax.group'].search([]):
            if '15%' in tg.name or 'Pajak' in tg.name or 'Tax' in tg.name:
                tg.write({'name': 'PPN 11%'})

        # 3. Update company details & bank
        comp = env['res.company'].search([], limit=1)
        comp.write({
            'name': 'PT Big Frozen Food',
            'vat': '01.234.567.8-651.000',
            'street': 'Jl. Industri Cold Storage No. 123',
            'street2': 'Kawasan Industri PIER',
            'city': 'Pasuruan',
            'zip': '67111',
            'phone': '0343-421999',
            'email': 'info@bigfrozenfood.co.id',
            'website': 'www.bigfrozenfood.co.id',
        })

        bca = env['res.bank'].search([('name', 'like', 'BCA')], limit=1)
        if not bca:
            bca = env['res.bank'].create({'name': 'Bank Central Asia (BCA)', 'bic': 'CENAIDJA'})

        bank_acc = env['res.partner.bank'].search([('partner_id', '=', comp.partner_id.id)], limit=1)
        if not bank_acc:
            env['res.partner.bank'].create({
                'partner_id': comp.partner_id.id,
                'bank_id': bca.id,
                'acc_number': '8730998877',
                'acc_holder_name': 'PT Big Frozen Food',
                'company_id': comp.id,
            })
        else:
            bank_acc.write({'company_id': comp.id, 'acc_holder_name': 'PT Big Frozen Food'})

        # 4. Bulletproof inline QWeb arch for unpatched wkhtmltopdf & web rendering
        new_arch = """<t t-name="account.report_invoice_document">
    <t t-call="web.basic_layout">
        <t t-set="o" t-value="o.with_context(lang=lang)"/>
        
        <style>
            @page {
                size: A4 portrait;
                margin: 10mm 12mm 12mm 12mm;
            }
            .inv-page {
                font-family: 'DejaVu Sans', Arial, Helvetica, sans-serif;
                color: #2c3e50;
                font-size: 11px;
                line-height: 1.4;
                width: 100%;
                padding: 10px;
            }
            .company-header-table {
                width: 100%;
                border-bottom: 2px solid #1a365d;
                padding-bottom: 8px;
                margin-bottom: 12px;
            }
            .company-title {
                font-size: 18px;
                font-weight: bold;
                color: #1a365d;
                margin: 0;
            }
            .company-details {
                font-size: 11px;
                color: #4a5568;
            }
            .doc-title-box {
                text-align: center;
                margin-bottom: 12px;
            }
            .doc-title-box h2 {
                font-size: 20px;
                font-weight: bold;
                color: #1a365d;
                margin: 0;
                letter-spacing: 1px;
            }
            .doc-title-box p {
                font-size: 10px;
                color: #718096;
                margin: 2px 0 0 0;
                font-weight: bold;
            }
            .meta-table {
                width: 100%;
                margin-bottom: 12px;
            }
            .meta-box {
                background-color: #f8fafc;
                border: 1px solid #cbd5e0;
                border-radius: 4px;
                padding: 10px;
                vertical-align: top;
            }
            .item-table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 12px;
            }
            .item-table th {
                background-color: #1a365d;
                color: #ffffff;
                font-size: 10px;
                font-weight: bold;
                text-transform: uppercase;
                padding: 8px 6px;
                border: 1px solid #1a365d;
            }
            .item-table td {
                padding: 7px 6px;
                border: 1px solid #e2e8f0;
                font-size: 11px;
            }
            .item-table tr:nth-child(even) {
                background-color: #f8fafc;
            }
            .bank-box {
                background-color: #ebf8ff;
                border: 1px solid #bee3f8;
                border-left: 4px solid #3182ce;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 11px;
            }
            .totals-table {
                width: 100%;
                border-collapse: collapse;
            }
            .totals-table td {
                padding: 5px 8px;
                font-size: 11px;
            }
            .sig-table {
                width: 100%;
                margin-top: 20px;
                text-align: center;
                font-size: 11px;
                page-break-inside: avoid;
            }
        </style>

        <div class="inv-page">
            <!-- Hidden structure node for POS / stock inheritance compatibility -->
            <div name="origin" class="d-none">
                <span t-field="o.invoice_origin"/>
            </div>

            <!-- Inline Company Header (Logo & Company Info) -->
            <table class="company-header-table">
                <tr>
                    <td style="width: 55%; vertical-align: top;">
                        <img t-if="o.company_id.logo" t-att-src="image_data_uri(o.company_id.logo)" style="max-height: 60px; max-width: 200px;" alt="Logo"/>
                        <div class="company-title" t-field="o.company_id.name"/>
                        <div class="company-details">
                            <span t-field="o.company_id.street"/>, <span t-field="o.company_id.street2"/><br/>
                            <span t-field="o.company_id.city"/> <span t-field="o.company_id.zip"/><br/>
                            Telp: <span t-field="o.company_id.phone"/> | Email: <span t-field="o.company_id.email"/>
                        </div>
                    </td>
                    <td style="width: 45%; vertical-align: top; text-align: right;">
                        <div style="font-weight: bold; font-size: 11px; color: #1a365d;">
                            NPWP Penjual:
                        </div>
                        <div style="font-family: monospace; font-size: 12px; font-weight: bold; color: #2d3748;">
                            <span t-field="o.company_id.vat"/>
                        </div>
                        <div style="margin-top: 5px; font-size: 10px; color: #718096;">
                            Website: <span t-field="o.company_id.website"/>
                        </div>
                    </td>
                </tr>
            </table>

            <!-- Document Title -->
            <div class="doc-title-box">
                <h2>FAKTUR PENJUALAN</h2>
                <p>SALES INVOICE</p>
            </div>

            <!-- Customer & Invoice Info Table Grid -->
            <table class="meta-table">
                <tr>
                    <!-- Kiri: Kepada Yth (Customer) -->
                    <td style="width: 58%; padding-right: 8px; vertical-align: top;">
                        <div class="meta-box">
                            <strong style="color: #1a365d; font-size: 11px; text-transform: uppercase;">Kepada Yth. / Diterbitkan Untuk:</strong>
                            <div style="font-size: 13px; font-weight: bold; color: #2d3748; margin-top: 3px; margin-bottom: 2px;">
                                <span t-field="o.partner_id.name"/>
                            </div>
                            <div t-field="o.partner_id" t-options='{"widget": "contact", "fields": ["address", "phone", "email"], "no_marker": True}' style="color: #4a5568; font-size: 11px;"/>
                            <div t-if="o.partner_id.vat" style="margin-top: 5px; padding-top: 4px; border-top: 1px solid #e2e8f0;">
                                <strong style="color: #2d3748;">NPWP Pembeli:</strong> <span t-field="o.partner_id.vat" style="font-family: monospace; font-weight: bold;"/>
                            </div>
                        </div>
                    </td>

                    <!-- Kanan: Detail Faktur -->
                    <td style="width: 42%; vertical-align: top;">
                        <div class="meta-box">
                            <table style="width: 100%; font-size: 11px;">
                                <tr>
                                    <td style="padding: 2px 0; font-weight: bold; color: #4a5568;">No. Faktur:</td>
                                    <td style="padding: 2px 0; font-weight: bold; color: #1a365d; text-align: right;"><span t-field="o.name"/></td>
                                </tr>
                                <tr>
                                    <td style="padding: 2px 0; color: #4a5568;">Tanggal Faktur:</td>
                                    <td style="padding: 2px 0; text-align: right;"><span t-field="o.invoice_date"/></td>
                                </tr>
                                <tr>
                                    <td style="padding: 2px 0; color: #4a5568;">Jatuh Tempo:</td>
                                    <td style="padding: 2px 0; text-align: right;"><span t-field="o.invoice_date_due"/></td>
                                </tr>
                                <tr t-if="o.invoice_payment_term_id">
                                    <td style="padding: 2px 0; color: #4a5568;">Syarat Pembayaran:</td>
                                    <td style="padding: 2px 0; text-align: right;"><span t-field="o.invoice_payment_term_id.name"/></td>
                                </tr>
                                <tr t-if="o.ref or o.invoice_origin">
                                    <td style="padding: 2px 0; color: #4a5568;">No. Referensi / PO:</td>
                                    <td style="padding: 2px 0; text-align: right;"><span t-out="o.ref or o.invoice_origin"/></td>
                                </tr>
                            </table>
                        </div>
                    </td>
                </tr>
            </table>

            <!-- Product Table -->
            <table class="item-table">
                <thead>
                    <tr>
                        <th style="width: 6%; text-align: center;">No.</th>
                        <th style="width: 44%;">Nama Barang / Deskripsi</th>
                        <th style="width: 10%; text-align: center;">Banyaknya</th>
                        <th style="width: 10%; text-align: center;">Satuan</th>
                        <th style="width: 15%; text-align: right;">Harga Satuan (Rp)</th>
                        <th style="width: 15%; text-align: right;">Total Harga (Rp)</th>
                    </tr>
                </thead>
                <tbody>
                    <t t-set="lines" t-value="o.invoice_line_ids.filtered(lambda l: not l.display_type or l.display_type == 'product')"/>
                    <t t-set="line_num" t-value="0"/>
                    <tr t-foreach="lines" t-as="line" style="page-break-inside: avoid;">
                        <t t-set="line_num" t-value="line_num + 1"/>
                        <td style="text-align: center; vertical-align: middle;"><t t-out="line_num"/></td>
                        <td name="account_invoice_line_name" style="vertical-align: middle;">
                            <span t-field="line.name"/>
                        </td>
                        <td style="text-align: center; vertical-align: middle;">
                            <span t-field="line.quantity"/>
                        </td>
                        <td style="text-align: center; vertical-align: middle;">
                            <span t-out="line.product_uom_id.name or 'Pcs'"/>
                        </td>
                        <td style="text-align: right; vertical-align: middle;">
                            <span t-field="line.price_unit" t-options='{"widget": "monetary", "display_currency": o.currency_id}'/>
                        </td>
                        <td style="text-align: right; vertical-align: middle; font-weight: bold;">
                            <span t-field="line.price_subtotal" t-options='{"widget": "monetary", "display_currency": o.currency_id}'/>
                        </td>
                    </tr>
                </tbody>
            </table>

            <!-- Subtotal & Summary Section Grid -->
            <div class="row">
                <!-- Kiri: Informasi Transfer Bank -->
                <div class="col-7">
                    <div class="bank-box">
                        <strong style="color: #2b6cb0; font-size: 11px; text-transform: uppercase;">Pembayaran Transfer Bank:</strong>
                        <div style="margin-top: 4px; font-size: 11px; color: #2d3748; line-height: 1.4;">
                            <div><strong>Bank Central Asia (BCA)</strong>: 8730998877 a.n. PT Big Frozen Food</div>
                            <div><strong>Bank Mandiri</strong>: 1420099887700 a.n. PT Big Frozen Food</div>
                        </div>
                    </div>
                </div>

                <!-- Kanan: Totals Table (Preserving div id="right-elements") -->
                <div id="right-elements" class="col-5">
                    <table class="totals-table">
                        <tr>
                            <td style="color: #4a5568; font-weight: 500;">Subtotal (DPP):</td>
                            <td style="text-align: right; font-weight: bold;"><span t-field="o.amount_untaxed" t-options='{"widget": "monetary", "display_currency": o.currency_id}'/></td>
                        </tr>
                        <tr>
                            <td style="color: #4a5568; font-weight: 500;">PPN (11%):</td>
                            <td style="text-align: right; font-weight: bold;"><span t-field="o.amount_tax" t-options='{"widget": "monetary", "display_currency": o.currency_id}'/></td>
                        </tr>
                        <tr style="border-top: 2px solid #1a365d; border-bottom: 2px solid #1a365d; background-color: #f8fafc;">
                            <td style="color: #1a365d; font-weight: bold; font-size: 12px; padding-top: 5px; padding-bottom: 5px;">Total Tagihan:</td>
                            <td style="text-align: right; font-weight: bold; font-size: 12px; color: #1a365d; padding-top: 5px; padding-bottom: 5px;"><span t-field="o.amount_total" t-options='{"widget": "monetary", "display_currency": o.currency_id}'/></td>
                        </tr>
                        <t t-set="payments_vals" t-value="o._get_reconciled_invoices_partials()[0]"/>
                        <t t-if="payments_vals">
                            <tr t-foreach="payments_vals" t-as="payment_vals">
                                <td style="color: #2f855a; font-size: 10px;">
                                    <i class="oe_payment_label">Dibayar pada <span t-out="payment_vals.get('date')"/></i>:
                                </td>
                                <td style="text-align: right; color: #2f855a; font-weight: bold; font-size: 10px;">
                                    <span t-out="payment_vals.get('amount')" t-options='{"widget": "monetary", "display_currency": o.currency_id}'/>
                                </td>
                            </tr>
                        </t>
                        <tr t-if="o.payment_state != 'invoiced'" style="border-top: 1px dashed #cbd5e0;">
                            <td style="color: #742a2a; font-weight: bold;">Sisa Tagihan:</td>
                            <td style="text-align: right; font-weight: bold; color: #742a2a;"><span t-field="o.amount_residual" t-options='{"widget": "monetary", "display_currency": o.currency_id}'/></td>
                        </tr>
                    </table>
                </div>
            </div>

            <div id="payment_term" class="clearfix">
                <div class="d-none">
                    <p name="payment_communication">
                        Payment Reference: <span t-field="o.payment_reference"/>
                        <t t-if="o.partner_bank_id"> on this account: <span t-field="o.partner_bank_id"/></t>
                    </p>
                </div>
                <div id="qrcode" class="d-none"/>
            </div>

            <!-- Signature Section (Tanda Tangan) -->
            <table class="sig-table">
                <tr>
                    <td style="width: 50%;">
                        <div>Penerima / Pembeli,</div>
                        <div style="height: 45px;"/>
                        <div><strong>( ........................................... )</strong></div>
                    </td>
                    <td style="width: 50%;">
                        <div>Pasuruan, <span t-out="o.invoice_date or datetime.datetime.now().strftime('%d/%m/%Y')"/></div>
                        <div>Hormat Kami,</div>
                        <div style="font-weight: bold; color: #1a365d;">PT Big Frozen Food</div>
                        <div style="height: 35px;"/>
                        <div><strong>( ........................................... )</strong></div>
                    </td>
                </tr>
            </table>
        </div>
    </t>
</t>"""

        # Update account.report_invoice_document
        v_main = env.ref('account.report_invoice_document')
        v_main.write({'arch': new_arch})

        # Synchronize child primary views
        v_preview = env.ref('account.report_invoice_document_preview', raise_if_not_found=False)
        if v_preview:
            v_preview.write({'arch': new_arch})

        v_edi = env.ref('account_edi_ubl_cii.report_invoice_document', raise_if_not_found=False)
        if v_edi:
            v_edi.write({'arch': new_arch, 'active': True})

        cr.commit()
        print("=== SUCCESS: BULLETPROOF INLINE PDF & WEB TEMPLATE APPLIED SUCCESSFULLY ===")

if __name__ == '__main__':
    run()
