import { patch } from '@web/core/utils/patch';
import { useService, useBus } from '@web/core/utils/hooks';

import { NavBar } from '@web/webclient/navbar/navbar';
import { AppsMenu } from "@muk_web_theme/webclient/appsmenu/appsmenu";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.appMenuService = useService('app_menu');
        try {
            this.actionService = useService('action');
        } catch (e) {
            // fallback if action service not registered in this context
        }
        try {
            this.router = useService('router');
        } catch (e) {
            // fallback
        }

        if (this.env && this.env.bus) {
            useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => this.render());
        }
    },
    isSectionActive(section) {
        if (!section) return false;

        const currentMenuId = this.router?.current?.menu_id 
            || this.actionService?.currentController?.config?.menuId;
        const currentActionId = this.router?.current?.action 
            || this.actionService?.currentController?.action?.id;
        const currentActionXmlId = this.actionService?.currentController?.action?.xmlid;

        const checkNode = (node) => {
            if (!node) return false;

            // Direct ID match
            if (currentMenuId && (node.id == currentMenuId || node.xmlid == currentMenuId)) {
                return true;
            }

            // Action match
            if (currentActionId && (node.actionID == currentActionId || node.actionID === currentActionId)) {
                return true;
            }

            if (currentActionXmlId && node.xmlid === currentActionXmlId) {
                return true;
            }

            // URL hash / pathname fallback
            const hash = window.location.hash || '';
            const path = window.location.pathname || '';
            if (node.id && (hash.includes(`menu_id=${node.id}`) || path.includes(`menu-${node.id}`))) {
                return true;
            }
            if (node.actionID && (hash.includes(`action=${node.actionID}`) || path.includes(`action-${node.actionID}`))) {
                return true;
            }

            // Check children recursively
            if (node.childrenTree && node.childrenTree.length) {
                return node.childrenTree.some(c => checkNode(c));
            }

            return false;
        };

        return checkNode(section);
    },
});

patch(NavBar, {
    components: {
        ...NavBar.components,
        AppsMenu,
    },
});

