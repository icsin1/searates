# -*- coding: utf-8 -*-

from . import models
from . import wizard
from . import report

from odoo import api, SUPERUSER_ID


def _create_quote_history(cr, registry):
    """ This is used to update quote status history """
    env = api.Environment(cr, SUPERUSER_ID, {})

    cr.execute(""" SELECT id, res_id from mail_message where model = 'shipment.quote' and message_type = 'notification' """)
    result = cr.fetchall()

    mail_message_obj = env['mail.message']
    shipment_quote_obj = env['shipment.quote']

    quote_mapping_dict = {
        'Draft': 'draft',
        'Sent': 'sent',
        'Expired': 'expire',
        'Cancelled': 'cancel',
        'Accepted': 'accept',
        'Rejected': 'reject',
        'To Approve': 'to_approve',
        'Approved': 'approved',
        }

    for message_id, rec_id in result:
        message_id = mail_message_obj.browse(message_id)
        rec_id = shipment_quote_obj.browse(rec_id)
        if not rec_id:
            continue

        for tracking_value in message_id.tracking_value_ids.filtered(lambda l: l.field_desc == 'Status' and l.field_type == 'selection'):
            rec_id.status_history_ids.sudo().create({
                'quote_id': rec_id.id,
                'user_id': message_id.create_uid.id,
                'status': quote_mapping_dict[tracking_value.new_value_char],
                'status_change_date': message_id.date
                })
