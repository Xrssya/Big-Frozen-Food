/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MonetaryField } from "@web/views/fields/monetary/monetary_field";
import { FloatField } from "@web/views/fields/float/float_field";
import { getCurrency } from "@web/core/currency";
import { formatMonetary } from "@web/views/fields/formatters";

/**
 * BIG FROZEN FOOD - Remove ,00 from all monetary & float fields
 *
 * Root cause: when decimal.precision = 0, Odoo returns digits: False
 * formatFloat then falls back to precision = 2 → displays ,00
 *
 * Fix: Always force [69, 0] for IDR (Rp) currency regardless of field_digits option.
 */
patch(MonetaryField.prototype, {
    get currencyDigits() {
        // Get actual currency
        const currency = this.currency;
        if (currency) {
            const currencyData = getCurrency(this.currencyId);
            if (currencyData) {
                // If currency has 0 decimal places (IDR/Rp), always return [69, 0]
                if (currencyData.digits && currencyData.digits[1] === 0) {
                    return [69, 0];
                }
                // Also force 0 if symbol is Rp (safety net)
                if (currencyData.symbol === "Rp") {
                    return [69, 0];
                }
            }
        }
        // Fall back to default behavior for other currencies
        if (this.props.useFieldDigits) {
            const fieldDigits = this.props.record.fields[this.props.name].digits;
            // If digits is False/null (meaning precision=0 in Odoo), return [69, 0]
            if (fieldDigits === false || fieldDigits === null) {
                return [69, 0];
            }
            return fieldDigits;
        }
        if (!currency) {
            return null;
        }
        return getCurrency(this.currencyId).digits;
    },

    get formattedValue() {
        if (this.props.inputType === "number" && !this.props.readonly && this.value) {
            return this.value;
        }
        const digits = this.currencyDigits;
        return formatMonetary(this.value, {
            digits: digits,
            minDigits: 0,
            currencyId: this.currencyId,
            noSymbol: !this.props.readonly || this.props.hideSymbol,
        });
    }
});

