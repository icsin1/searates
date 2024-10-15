# -*- coding: utf-8 -*-


def migrate(cr, version):
    # Migrate Existing State Record ID
    # NOTE Keeping this migration in ics_account module instead l10n_in_account_edi
    #   to manage XML-ID update with module sequence with change in l10n_in odoo-base module
    cr.execute("""
            UPDATE ir_model_data
                SET module = 'l10n_in'
                WHERE model = 'res.country.state'
                AND name = 'state_in_oc'
                AND module = 'l10n_in_account_edi';
        """)
