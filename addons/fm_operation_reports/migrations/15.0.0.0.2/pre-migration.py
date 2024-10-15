# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute("UPDATE ir_model_data SET noupdate='f' WHERE name='action_outstanding_customer_statement' AND module='fm_operation_reports'")
