# -*- coding: utf-8 -*-


def migrate(cr, version):
    cr.execute("DROP VIEW IF EXISTS house_cost_revenue_report")
    cr.execute("DROP VIEW IF EXISTS master_cost_revenue_report")
