odoo.define('ics_customer_portal_quote.portal_new', function (require) {
'use strict';

$(document).ready(function() {
	$("select[name='origin_country_id']").change(function() {		
        $.ajax({
                type: "POST",
                dataType: 'json',
                url: '/fetch_un_locations_based_on_country',
                contentType: "application/json; charset=utf-8",
                data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'country_id': $(this).val(),'location_mode':'Origin'}}),
                success: function (data) {
                    $("select[name='origin_id']").html(data.result)
                },
                error: function (data) {
                    console.error("ERROR ", data);
                },
            });
        });
		
	$("select[name='destination_country_id']").change(function() {		
		$.ajax({
            type: "POST",
            dataType: 'json',
            url: '/fetch_un_locations_based_on_country',
            contentType: "application/json; charset=utf-8",
            data: JSON.stringify({'jsonrpc': "2.0", 'method': "call", "params": {'country_id': $(this).val(),'location_mode':'Destination'}}),
            success: function (data) {
                $("select[name='destination_id']").html(data.result)
            },
            error: function (data) {
                console.error("ERROR ", data);
            },
        });
    });
});

});
