/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, useState } from "@odoo/owl";

export class CicilanDueDatePopup extends Component {
    static template = "bff_pos_cicilan.CicilanDueDatePopup";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        confirmLabel: { type: String, optional: true },
        dueDate: { type: [String, Boolean], optional: true },
        getPayload: Function,
        close: Function,
    };
    static defaultProps = {
        confirmLabel: _t("Simpan Batas Waktu"),
        title: _t("🗓️ Batas Waktu / Jatuh Tempo Cicilan"),
    };

    setup() {
        super.setup();
        const initialDate = (typeof this.props.dueDate === "string" && this.props.dueDate) ? this.props.dueDate : this._addDays(30);
        this.state = useState({
            selectedDate: initialDate,
            activePreset: this._detectPreset(initialDate),
        });
    }

    _today() {
        return new Date().toISOString().split("T")[0];
    }

    _addDays(days) {
        const d = new Date();
        d.setDate(d.getDate() + days);
        return d.toISOString().split("T")[0];
    }

    _detectPreset(dateStr) {
        const presets = [7, 14, 30, 60];
        for (const days of presets) {
            if (dateStr === this._addDays(days)) {
                return days;
            }
        }
        return "custom";
    }

    selectPreset(days) {
        this.state.selectedDate = this._addDays(days);
        this.state.activePreset = days;
    }

    onDateInput(ev) {
        const val = ev.target.value;
        if (val) {
            this.state.selectedDate = val < this._today() ? this._today() : val;
            this.state.activePreset = "custom";
        }
    }

    get formattedInputDate() {
        if (!this.state.selectedDate) return "";
        try {
            const parts = this.state.selectedDate.split("-");
            if (parts.length === 3) {
                return `${parts[2]}/${parts[1]}/${parts[0]}`;
            }
        } catch (e) {}
        return this.state.selectedDate;
    }

    onTextDateInput(ev) {
        const val = ev.target.value.trim();
        if (!val) return;
        const parts = val.split(/[\/\.-]/);
        if (parts.length === 3) {
            const day = parts[0].padStart(2, "0");
            const month = parts[1].padStart(2, "0");
            const year = parts[2].length === 2 ? "20" + parts[2] : parts[2];
            const isoDate = `${year}-${month}-${day}`;
            const d = new Date(isoDate);
            if (!isNaN(d.getTime())) {
                this.state.selectedDate = isoDate < this._today() ? this._today() : isoDate;
                this.state.activePreset = "custom";
            }
        }
    }

    get formattedTargetDate() {
        if (!this.state.selectedDate) return "";
        try {
            const parts = this.state.selectedDate.split("-");
            if (parts.length === 3) {
                const day = parts[2];
                const month = parts[1];
                const year = parts[0];
                const MONTH_NAMES = [
                    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                    "Juli", "Agustus", "September", "Oktober", "November", "Desember"
                ];
                const monthIdx = parseInt(month, 10) - 1;
                const monthName = MONTH_NAMES[monthIdx] || month;
                return `${day}/${month}/${year} (${parseInt(day, 10)} ${monthName} ${year})`;
            }
        } catch (e) {}
        return this.state.selectedDate;
    }

    confirm() {
        const finalDate = this.state.selectedDate < this._today() ? this._today() : this.state.selectedDate;
        this.props.getPayload(finalDate);
        this.props.close();
    }
}

patch(PosOrder.prototype, {
    setup(vals) {
        super.setup(...arguments);
        if (vals && vals.due_date) {
            this.due_date = vals.due_date;
        }
    },

    set_due_date(dueDate) {
        this.due_date = dueDate;
    },

    get_due_date() {
        return this.due_date;
    },

    serialize() {
        const data = super.serialize(...arguments);
        if (this.due_date) {
            data.due_date = this.due_date;
        }
        return data;
    },
});

patch(PaymentScreen.prototype, {
    async addNewPaymentLine(paymentMethod) {
        const res = await super.addNewPaymentLine(...arguments);
        if (paymentMethod && (paymentMethod.is_cicilan || (paymentMethod.name && paymentMethod.name.toLowerCase().includes("cicilan")))) {
            // Prompt popup due date when Cicilan payment method is selected
            this.dialog.add(CicilanDueDatePopup, {
                dueDate: this.currentOrder ? this.currentOrder.get_due_date() : false,
                getPayload: (selectedDate) => {
                    if (this.currentOrder) {
                        this.currentOrder.set_due_date(selectedDate);
                    }
                },
            });
        }
        return res;
    },

    async validateOrder(isForceValidate) {
        const order = this.currentOrder;
        if (order) {
            const hasCicilanLine = order.payment_ids.some((line) => {
                const pm = line.payment_method_id;
                return pm && (pm.is_cicilan || (pm.name && pm.name.toLowerCase().includes("cicilan")));
            });

            if (hasCicilanLine) {
                // 1. Mandat wajib isi Pelanggan
                if (!order.get_partner()) {
                    this.dialog.add(AlertDialog, {
                        title: _t("⛔ PELANGGAN WAJIB DIPILIH"),
                        body: _t(
                            "Anda menggunakan metode pembayaran Cicilan!\n\n" +
                            "Wajib memilih nama pelanggan terlebih dahulu agar sisa tagihan & histori cicilan dapat dicatat dan diproses pada modul Penagihan (Invoicing)."
                        ),
                    });
                    return;
                }

                // 2. Mandat wajib isi Batas Waktu / Tanggal Jatuh Tempo
                if (!order.get_due_date()) {
                    this.dialog.add(CicilanDueDatePopup, {
                        dueDate: order.get_due_date() || false,
                        getPayload: (selectedDate) => {
                            order.set_due_date(selectedDate);
                        },
                    });
                    return;
                }

                // 3. Otomatis set to_invoice = True agar invoice diterbitkan di backend
                order.set_to_invoice(true);
            }
        }
        return await super.validateOrder(...arguments);
    }
});

