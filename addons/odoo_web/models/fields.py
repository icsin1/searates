from odoo.fields import Integer, Float, Monetary

Integer.convert_to_export = lambda _, value, __: value
Float.convert_to_export = lambda _, value, __: value
Monetary.convert_to_export = lambda _, value, __: value
