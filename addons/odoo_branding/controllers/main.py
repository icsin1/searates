import functools

import odoo
from odoo.addons.web.controllers.main import Binary
from odoo.modules import get_resource_path
from odoo.addons.web.controllers.main import db_monodb
from odoo import http
from odoo.http import request


class MyBinaryController(Binary):

    @http.route([
        '/web/binary/company_logo',
        '/logo',
        '/logo.png',
    ], type='http', auth="none", cors="*")
    def company_logo(self, dbname=None, **kw):
        placeholder = functools.partial(get_resource_path, 'base', 'static', 'img')
        uid = None
        if request.session.db:
            dbname = request.session.db
            uid = request.session.uid
        elif dbname is None:
            dbname = db_monodb()

        if not uid:
            uid = odoo.SUPERUSER_ID

        if not dbname:
            response = http.send_file(placeholder('res_company_logo.png'))
        else:
            try:
                # create an empty registry
                registry = odoo.modules.registry.Registry(dbname)
                with registry.cursor() as cr:
                    company = int(kw['company']) if kw and kw.get('company') else False
                    if company:
                        cr.execute("""SELECT logo_web, write_date
                                        FROM res_company
                                    WHERE id = %s
                                """, (company,))
                    else:
                        cr.execute("""SELECT c.logo_web, c.write_date
                                        FROM res_users u
                                LEFT JOIN res_company c
                                        ON c.id = u.company_id
                                    WHERE u.id = %s
                                """, (uid,))
                    row = cr.fetchone()
                    if row and row[0]:
                        response = super(MyBinaryController, self).company_logo(dbname=None, **kw)
                    else:
                        response = http.send_file(placeholder('res_company_logo.png'))  # Replaced with our custom logo file name
            except Exception:
                response = http.send_file(placeholder('res_company_logo.png'))

        return response
