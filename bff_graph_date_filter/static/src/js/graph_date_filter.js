import { Component, useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { GraphRenderer } from "@web/views/graph/graph_renderer";
import { serializeDate, serializeDateTime } from "@web/core/l10n/dates";
import { DateTimeInput } from "@web/core/datetime/datetime_input";

const { DateTime } = luxon;

export class GraphDateFilter extends Component {
    static template = "bff_graph_date_filter.GraphDateFilter";
    static components = { DateTimeInput };
    static props = {
        model: Object,
    };

    setup() {
        this.state = useState({
            selectedPreset: "all",
            startDate: DateTime.now().startOf("month"),
            endDate: DateTime.now().endOf("day"),
        });
        this.activeFilterGroupId = null;
    }

    onStartDateChange(val) {
        if (val) {
            this.state.startDate = val;
            this.state.selectedPreset = "custom";
            this.applyCustomDate();
        }
    }

    onEndDateChange(val) {
        if (val) {
            this.state.endDate = val;
            this.state.selectedPreset = "custom";
            this.applyCustomDate();
        }
    }

    getDateField() {
        const searchFields = this.env.searchModel ? this.env.searchModel.searchViewFields : {};
        const metaFields = (this.props.model && this.props.model.metaData && this.props.model.metaData.fields) || {};

        const preferredNames = ["date", "date_order", "create_date", "date_done", "invoice_date", "accounting_date"];
        for (const name of preferredNames) {
            if (searchFields[name] || metaFields[name]) {
                return name;
            }
        }

        for (const [name, field] of Object.entries(searchFields)) {
            if (field && (field.type === "date" || field.type === "datetime")) {
                return name;
            }
        }
        for (const [name, field] of Object.entries(metaFields)) {
            if (field && (field.type === "date" || field.type === "datetime")) {
                return name;
            }
        }

        return "create_date";
    }

    getDateFieldType(fieldName) {
        const searchFields = this.env.searchModel ? this.env.searchModel.searchViewFields : {};
        const metaFields = (this.props.model && this.props.model.metaData && this.props.model.metaData.fields) || {};

        const field = searchFields[fieldName] || metaFields[fieldName];
        return field ? field.type : "datetime";
    }

    clearExistingFilter() {
        if (this.activeFilterGroupId && this.env.searchModel) {
            this.env.searchModel.deactivateGroup(this.activeFilterGroupId);
            this.activeFilterGroupId = null;
        }
    }

    applyDomain(presetName, domain) {
        this.clearExistingFilter();
        if (!domain || !domain.length) {
            return;
        }
        if (this.env.searchModel) {
            const preFilters = [{
                description: `Filter Tanggal: ${presetName}`,
                domain: JSON.stringify(domain),
                custom: true,
            }];
            const created = this.env.searchModel.createNewFilters(preFilters);
            if (created && created.length) {
                this.activeFilterGroupId = created[0].groupId;
            }
        }
    }

    selectPreset(preset) {
        this.state.selectedPreset = preset;
        if (preset === "all") {
            this.clearExistingFilter();
            return;
        }

        const dateField = this.getDateField();
        const fieldType = this.getDateFieldType(dateField);

        const now = DateTime.now();
        let startDt = null;
        let endDt = null;
        let label = "";

        if (preset === "this_month") {
            startDt = now.startOf("month");
            endDt = now.endOf("month");
            label = "Bulan Ini";
        } else if (preset === "30days") {
            startDt = now.minus({ days: 30 }).startOf("day");
            endDt = now.endOf("day");
            label = "30 Hari Terakhir";
        } else if (preset === "this_year") {
            startDt = now.startOf("year");
            endDt = now.endOf("year");
            label = "Tahun Ini";
        }

        if (startDt && endDt) {
            this.state.startDate = startDt;
            this.state.endDate = endDt;

            const startStr = fieldType === "date"
                ? serializeDate(startDt)
                : serializeDateTime(startDt);
            const endStr = fieldType === "date"
                ? serializeDate(endDt)
                : serializeDateTime(endDt);

            const domain = [
                [dateField, ">=", startStr],
                [dateField, "<=", endStr],
            ];
            this.applyDomain(label, domain);
        }
    }

    applyCustomDate() {
        if (!this.state.startDate || !this.state.endDate) {
            return;
        }

        const dateField = this.getDateField();
        const fieldType = this.getDateFieldType(dateField);

        const startDt = typeof this.state.startDate === "string"
            ? DateTime.fromISO(this.state.startDate).startOf("day")
            : this.state.startDate.startOf("day");
        const endDt = typeof this.state.endDate === "string"
            ? DateTime.fromISO(this.state.endDate).endOf("day")
            : this.state.endDate.endOf("day");

        const startStr = fieldType === "date"
            ? serializeDate(startDt)
            : serializeDateTime(startDt);
        const endStr = fieldType === "date"
            ? serializeDate(endDt)
            : serializeDateTime(endDt);

        const domain = [
            [dateField, ">=", startStr],
            [dateField, "<=", endStr],
        ];
        const label = `${startDt.toFormat("dd/MM/yyyy")} s/d ${endDt.toFormat("dd/MM/yyyy")}`;
        this.applyDomain(label, domain);
    }
}

patch(GraphRenderer, {
    components: {
        ...GraphRenderer.components,
        GraphDateFilter,
    },
});
