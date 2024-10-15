# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute("DROP VIEW IF EXISTS operation_sale_report")
