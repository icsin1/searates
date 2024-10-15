# -*- coding: utf-8 -*-

from odoo import models, fields


class FreightUnLocation(models.Model):
    _inherit = "freight.un.location"

    location_type_id = fields.Many2one('freight.location.type', string="Location Type")
