# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # As default is pdf for all, moving this to html preview otherwise stimulsoft viewer will be not loaded
    mrt_docs = env['stimulsoft.mrt.report'].search([('output_type', '=', 'pdf')])
    mrt_docs.write({'output_type': 'html'})
