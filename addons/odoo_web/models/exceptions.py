# -*- coding: utf-8 -*-
from odoo.exceptions import RedirectWarning


class RedirectToWarning(RedirectWarning):
    """ Warning with a possibility to redirect the specific record instead of simply
        displaying the warning message.
    """
