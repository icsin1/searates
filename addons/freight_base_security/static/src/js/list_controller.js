odoo.define('freight_base_security.tree.quick_create', function (require) {
"use strict";
    var ListController = require('web.ListController');
    var ListView = require('web.ListView');
    var viewRegistry = require('web.view_registry');

    var QuickCreateListController = ListController.extend({
        buttons_template: 'ListView.buttons.QuickCreate',
        events: _.extend({}, ListController.prototype.events, {
            'click .o_button_quick_create': '_onQuickCreate',
        }),
        _onQuickCreate: function (ev) {
            return this.do_action({
                type: 'ir.actions.act_window',
                res_model: this.modelName,
                views: [[false, 'form']],
                context: {'form_view_ref': 'freight_base_security.view_users_simple_form_freight_base_security'},
                target: 'new'
            }, {
                on_close: this.reload.bind(this, {})
            });
        }
    });

    var QuickCreateListView = ListView.extend({
        config: _.extend({}, ListView.prototype.config, {
            Controller: QuickCreateListController,
        }),
    });

    viewRegistry.add('quick_create_button', QuickCreateListView);
});
