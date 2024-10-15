odoo.define('odoo_branding.AbstractWebClient', function (require) {
"use strict";

var AbstractWebClient = require('web.AbstractWebClient');
AbstractWebClient.include({
    init: function () {
        this._super.apply(this, arguments);
        this.set('title_part', {"zopenerp": "Welcome"});
    }
});
    
});    