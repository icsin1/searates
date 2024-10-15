
def migrate(cr, registry):

    query = "UPDATE ir_module_module SET active=false WHERE to_buy=true"
    cr.execute(query)
