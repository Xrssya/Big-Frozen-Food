/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { ProxyStatus } from "@point_of_sale/app/navbar/proxy_status/proxy_status";
import { SaleDetailsButton } from "@point_of_sale/app/navbar/sale_details_button/sale_details_button";
import { CashMovePopup } from "@point_of_sale/app/navbar/cash_move_popup/cash_move_popup";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { BackButton } from "@point_of_sale/app/screens/product_screen/action_pad/back_button/back_button";
import { CashierName } from "@point_of_sale/app/navbar/cashier_name/cashier_name";
import { OrderTabs } from "@point_of_sale/app/components/order_tabs/order_tabs";
import { ClosePosPopup } from "@point_of_sale/app/navbar/closing_popup/closing_popup";
import { Input } from "@point_of_sale/app/generic_components/inputs/input/input";
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { Numpad } from "@point_of_sale/app/generic_components/numpad/numpad";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";

ProductScreen.components = {
    ...ProductScreen.components,
    ProxyStatus,
    SaleDetailsButton,
    BackButton,
    CashierName,
    OrderTabs,
    Input,
    ProductCard,
    OrderSummary,
    ControlButtons,
    Numpad,
    ActionpadWidget,
};

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        try {
            this.hardwareProxy = useService("hardware_proxy");
        } catch (e) {
            // Optional service fallback
        }
        this.selectedCategoryId = null;
    },
    setSelectedCategory(categoryId) {
        this.selectedCategoryId = categoryId;
        if (this.pos && typeof this.pos.setSelectedCategory === "function") {
            this.pos.setSelectedCategory(categoryId);
        }
    },
    async closeSession() {
        return this.pos ? this.pos.closeSession() : false;
    },
    onCashMoveButtonClick() {
        if (this.hardwareProxy && typeof this.hardwareProxy.openCashbox === "function") {
            this.hardwareProxy.openCashbox(_t("Cash in / out"));
        }
        if (this.dialog) {
            this.dialog.add(CashMovePopup);
        }
    },
    get orderCount() {
        return (this.pos && typeof this.pos.get_open_orders === "function") ? this.pos.get_open_orders().length : 0;
    },
    async onTicketButtonClick() {
        if (!this.pos) return;
        if (this.isTicketScreenShown) {
            this.pos.closeScreen();
        } else {
            if (this._shouldLoadOrders()) {
                try {
                    this.pos.setLoadingOrderState(true);
                    await this.pos.syncAllOrders();
                } finally {
                    this.pos.setLoadingOrderState(false);
                    this.pos.showScreen("TicketScreen");
                }
            } else {
                this.pos.showScreen("TicketScreen");
            }
        }
    },
    _shouldLoadOrders() {
        return this.pos && this.pos.config && this.pos.config.trusted_config_ids && this.pos.config.trusted_config_ids.length > 0;
    },
    showBackButton() {
        return this.pos && typeof this.pos.showBackButton === "function" && this.pos.showBackButton() && this.ui && this.ui.isSmall;
    },
    getOrderTabs() {
        return (this.pos && typeof this.pos.get_open_orders === "function") ? this.pos.get_open_orders().filter((order) => !order.table_id) : [];
    },
});