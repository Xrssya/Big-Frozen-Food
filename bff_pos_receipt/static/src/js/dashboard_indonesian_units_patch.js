/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import * as numberUtils from "@web/core/utils/numbers";

function indonesianUnits(str) {
    if (typeof str !== "string") return str;
    return str
        .replace(/(\d+(?:[\.,]\d+)?)\s*m\b/gi, "$1jt")
        .replace(/(\d+(?:[\.,]\d+)?)\s*k\b/gi, "$1rb")
        .replace(/(\d+(?:[\.,]\d+)?)\s*b\b/gi, "$1M");
}

// 1. Intercept Canvas fillText (used by Spreadsheet Scorecard Canvas rendering)
if (typeof CanvasRenderingContext2D !== "undefined" && !CanvasRenderingContext2D.prototype._idr_patched) {
    CanvasRenderingContext2D.prototype._idr_patched = true;
    const originalFillText = CanvasRenderingContext2D.prototype.fillText;
    CanvasRenderingContext2D.prototype.fillText = function (text, x, y, maxWidth) {
        if (typeof text === "string") {
            text = indonesianUnits(text);
        }
        if (maxWidth !== undefined) {
            return originalFillText.call(this, text, x, y, maxWidth);
        }
        return originalFillText.call(this, text, x, y);
    };
}

// 2. Patch humanNumber in @web/core/utils/numbers (used by web views & float fields)
if (numberUtils.humanNumber) {
    patch(numberUtils, {
        humanNumber(number, options) {
            const res = super.humanNumber(number, options);
            return indonesianUnits(res);
        },
    });
}

// 3. Patch o_spreadsheet ScorecardChart if present
function patchScorecard() {
    try {
        const spreadsheetExports = odoo.loader.get("@spreadsheet/o_spreadsheet/o_spreadsheet");
        const ScorecardChart = spreadsheetExports?.components?.ScorecardChart || spreadsheetExports?.ScorecardChart;
        if (ScorecardChart && !ScorecardChart._idr_patched) {
            ScorecardChart._idr_patched = true;
            patch(ScorecardChart.prototype, {
                get runtime() {
                    const runtime = super.runtime;
                    if (runtime && !runtime._idr_formatted) {
                        const formatted = { ...runtime };
                        if (typeof formatted.keyValue === "string") {
                            formatted.keyValue = indonesianUnits(formatted.keyValue);
                        }
                        if (typeof formatted.baselineDisplay === "string") {
                            formatted.baselineDisplay = indonesianUnits(formatted.baselineDisplay);
                        }
                        formatted._idr_formatted = true;
                        return formatted;
                    }
                    return runtime;
                },
            });
        }
    } catch (e) {
        // Module not loaded yet or not installed
    }
}

patchScorecard();
