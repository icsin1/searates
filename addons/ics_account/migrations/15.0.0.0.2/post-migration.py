# -*- coding: utf-8 -*-


def migrate(cr, version):
    query = "UPDATE account_move SET label=name WHERE move_type != 'entry'"
    cr.execute(query)
