/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { ConnectionLostError } from "@web/core/network/rpc_service";
import { registry } from "@web/core/registry";

export const WebNotificationService = {
    dependencies: ["action", "notification", "rpc"],

    start(env, { action, notification, rpc }) {
        let notifTimeouts = {};
        let nextNotifTimeout = null;
        const displayedNotifications = new Set();

        env.bus.on("WEB_CLIENT_READY", null, async () => {
            const legacyEnv = owl.Component.env;
            legacyEnv.services.bus_service.onNotification(this, (notifications) => {
                for (const { payload, type } of notifications) {
                    if (type === "web.notification") {
                        displayWebNotification(payload);
                    }
                }
            });
            legacyEnv.services.bus_service.startPolling();
        });

        function displayWebNotification(notifications) {
            let lastNotifTimer = 0;

            browser.clearTimeout(nextNotifTimeout);
            Object.values(notifTimeouts).forEach((notif) => browser.clearTimeout(notif));
            notifTimeouts = {};

            notifications.forEach(async function (notif) {
                await rpc("/web_notification/notify_show", {'notif': notif});

                const key = notif.res_id + "," + notif.notification_id;
                notifTimeouts[key] = browser.setTimeout(function () {
                    const notificationRemove = notification.add(notif.message, {
                        title: notif.title,
                        type: "warning",
                        sticky: true,
                        messageIsHtml: true,
                        message: notif.message,
                        onClose: () => {
                            displayedNotifications.delete(key);
                        },
                        buttons: [
                            {
                                name: env._t("OK"),
                                primary: true,
                                onClick: async () => {
                                    await rpc("/web_notification/notify_ack", {'notif': notif});
                                    notificationRemove();
                                },
                            },
                            {
                                name: env._t("Details"),
                                onClick: async () => {
                                    await rpc("/web_notification/notify_details", {'notif': notif});
                                    await action.doAction({
                                        type: 'ir.actions.act_window',
                                        res_model: notif.res_model,
                                        res_id: notif.res_id,
                                        views: [[false, 'form']],
                                    }
                                    );
                                    notificationRemove();
                                },
                            },
                            {
                                name: env._t("Snooze"),
                                onClick: async () => {
                                    await rpc("/web_notification/notify_snooze", {'notif': notif});
                                    notificationRemove();
                                },
                            },
                        ],
                    });
                    displayedNotifications.add(key);
                }, notif.timer * 1000);
                lastNotifTimer = Math.max(lastNotifTimer, notif.timer);
            });

            if (lastNotifTimer > 0) {
                nextNotifTimeout = browser.setTimeout(
                    getNextNotif,
                    lastNotifTimer * 1000
                );
            }
        }

        async function getNextNotif() {
            try {
                const result = await rpc("/web_notification/notify_ack", {}, { silent: true });
                displayWebNotification(result);
            } catch (error) {
                if (!(error instanceof ConnectionLostError)) {
                    throw error;
                }
            }
        }
    },
};

registry.category("services").add("WebNotificationAlert", WebNotificationService);
