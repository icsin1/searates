odoo.define('ics_customer_portal_quote.portal_request_quote', function (require) {
'use strict';

var publicWidget = require('web.public.widget');
const Dialog = require('web.Dialog');
const {_t, qweb} = require('web.core');
const ajax = require('web.ajax');
const session = require('web.session');


publicWidget.registry.portalDetails = publicWidget.Widget.extend({
    selector: '.o_portal_request_quote',
    events: {
        'change select[name="transport_mode_id"]': '_onTransportModeChange',
        'change select[name="origin_country_id"]': '_onOriginCountryChange',
        'change select[name="destination_country_id"]': '_onDestinationCountryChange',

    },

    /**
     * @override
     */
    start: function () {
        var def = this._super.apply(this, arguments);

        this.$CargoType = this.$('select[name="cargo_type_id"]');

        this.$CargoTypeOptions = this.$CargoType.filter(':enabled').find('option:not(:first)');

        this.$Origin = this.$('select[name="origin_id"]');

        this.$OriginOptions = this.$Origin.filter(':enabled').find('option:not(:first)');

        this.$Destination = this.$('select[name="destination_id"]');

        this.$DestinationOptions = this.$Destination.filter(':enabled').find('option:not(:first)');

        this.$OriginPort = this.$('select[name="origin_port_id"]');

        this.$OriginPortOptions = this.$OriginPort.filter(':enabled').find('option:not(:first)');

        this.$DestinationPort = this.$('select[name="destination_port_id"]');

        this.$DestinationPortOptions = this.$DestinationPort.filter(':enabled').find('option:not(:first)');


        this._adaptCargoForm();
        this._adaptOriginCountryForm();
        this._adaptDestinationCountryForm();


        return def;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _adaptCargoForm: function () {
        var $TransportMode = this.$('select[name="transport_mode_id"]');
        var TransportModeID = ($TransportMode.val() || 0);
        this.$CargoTypeOptions.detach();
        var $displayedCargoType = this.$CargoTypeOptions.filter('[data-transport_mode_id=' + TransportModeID + ']');
        var nb = $displayedCargoType.appendTo(this.$CargoType).show().length;

        //extra
        var $OriginCountry = this.$('select[name="origin_country_id"]');
        var OriginCountryID = ($OriginCountry.val() || 0);
        this.$OriginOptions.detach();
        var $displayedOrigin = this.$OriginOptions.filter('[data-origin_country_id=' + OriginCountryID + ']');
        var nb = $displayedOrigin.appendTo(this.$Origin).show().length;

        this.$OriginPortOptions.detach();
        var $displayedOriginPort = this.$OriginPortOptions.filter('[data-transport_mode_id=' + TransportModeID + ']').filter('[data-origin_country_id=' + OriginCountryID + ']');
        var nb = $displayedOriginPort.appendTo(this.$OriginPort).show().length;

        this.$DestinationPortOptions.detach();
        var $DisplayedDestinationPort = this.$DestinationPortOptions.filter('[data-transport_mode_id=' + TransportModeID + ']').filter('[data-origin_country_id=' + OriginCountryID + ']');
        var nb = $DisplayedDestinationPort.appendTo(this.$DestinationPort).show().length;


//        this.$CargoType.parent().toggle(nb >= 1);
    },

    _adaptOriginCountryForm: function () {
        var $OriginCountry = this.$('select[name="origin_country_id"]');
        var OriginCountryID = ($OriginCountry.val() || 0);
        this.$OriginOptions.detach();
        var $displayedOrigin = this.$OriginOptions.filter('[data-origin_country_id=' + OriginCountryID + ']');
        var nb = $displayedOrigin.appendTo(this.$Origin).show().length;

        //extra
        var $TransportMode = this.$('select[name="transport_mode_id"]');
        var TransportModeID = ($TransportMode.val() || 0);
        this.$CargoTypeOptions.detach();
        var $displayedCargoType = this.$CargoTypeOptions.filter('[data-transport_mode_id=' + TransportModeID + ']');
        var nb = $displayedCargoType.appendTo(this.$CargoType).show().length;

        this.$OriginPortOptions.detach();
        var $displayedOriginPort = this.$OriginPortOptions.filter('[data-origin_country_id=' + OriginCountryID + ']').filter('[data-transport_mode_id=' + TransportModeID + ']');
        var nb = $displayedOriginPort.appendTo(this.$OriginPort).show().length;



//        this.$Origin.parent().toggle(nb >= 1);
    },

    _adaptDestinationCountryForm: function () {
        var $DestinationCountry = this.$('select[name="destination_country_id"]');
        var DestinationCountryID = ($DestinationCountry.val() || 0);
        this.$DestinationOptions.detach();
        var $DisplayedDestination = this.$DestinationOptions.filter('[data-destination_country_id=' + DestinationCountryID + ']');
        var nb = $DisplayedDestination.appendTo(this.$Destination).show().length;


        //extra
        var $TransportMode = this.$('select[name="transport_mode_id"]');
        var TransportModeID = ($TransportMode.val() || 0);
        this.$CargoTypeOptions.detach();
        var $displayedCargoType = this.$CargoTypeOptions.filter('[data-transport_mode_id=' + TransportModeID + ']');
        var nb = $displayedCargoType.appendTo(this.$CargoType).show().length;

        this.$DestinationPortOptions.detach();
        var $DisplayedDestinationPort = this.$DestinationPortOptions.filter('[data-destination_country_id=' + DestinationCountryID + ']').filter('[data-transport_mode_id=' + TransportModeID + ']');
        var nb = $DisplayedDestinationPort.appendTo(this.$DestinationPort).show().length;


//        this.$Origin.parent().toggle(nb >= 1);
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * @private
     */
    _onTransportModeChange: function () {
        this._adaptCargoForm();
    },

    _onOriginCountryChange: function () {
        this._adaptOriginCountryForm();
    },

    _onDestinationCountryChange: function () {
        this._adaptDestinationCountryForm();
    },
});

});
