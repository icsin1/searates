/** @odoo-module **/

import {
    WarningDialog,
    RedirectWarningDialog,
    odooExceptionTitleMap,
    RPCErrorDialog,
    SessionExpiredDialog,
    ErrorDialog
} from "@web/core/errors/error_dialogs";
import { Dialog } from "@web/core/dialog/dialog";
import { capitalize } from "@web/core/utils/strings";
import { patch } from 'web.utils';
import { NotificationRequest } from '@mail/components/notification_request/notification_request';

SessionExpiredDialog.title = 'Session Expired'
ErrorDialog.title = 'Error'
Dialog.title = 'SearatesERP'

patch(RedirectWarningDialog.prototype, 'RedirectWarningDialog', {
    setup() {
        this._super(...arguments);
        const { subType } = this.props;
        this.title = capitalize(subType) || this.env._t("Warning");
    }

});
patch(WarningDialog.prototype, 'WarningDialog', {
    setup() {
        this._super(...arguments);
        this.title = this.env._t("Warning");
    }

});
patch(RPCErrorDialog.prototype, 'RPCErrorDialog', {
    inferTitle() {
        if (this.props.exceptionName && odooExceptionTitleMap.has(this.props.exceptionName)) {
            this.title = odooExceptionTitleMap.get(this.props.exceptionName).toString();
            return;
        }
        if (!this.props.type) return;
        switch (this.props.type) {
            case "server":
                this.title = this.env._t("Server Error");
                break;
            case "script":
                this.title = this.env._t("Client Error");
                break;
            case "network":
                this.title = this.env._t("Network Error");
                break;
        }
    }

});

patch(NotificationRequest.prototype, 'NotificationRequest', {
    _handleResponseNotificationPermission(value) {
        this.messaging.refreshIsNotificationPermissionDefault();
        if (value !== 'granted') {
            this.env.services['bus_service'].sendNotification({
                message: this.env._t("System will not have the permission to send native notifications on this device."),
                title: this.env._t("Permission denied"),
            });
        }
    }
});
