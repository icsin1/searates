# -*- coding: utf-8 -*-

from odoo import models, _


class Invite(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    def add_followers(self):
        super().add_followers()
        for wizard in self:
            if wizard.partner_ids and wizard.res_model == 'crm.prospect.opportunity':
                record = self.env[wizard.res_model].browse(wizard.res_id)
                msg = "Followers is added : {} ".format(", ".join(wizard.partner_ids.mapped('name')))
                record.message_post(body=msg)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload'
        }
