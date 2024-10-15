# -*- coding: utf-8 -*-

from odoo import models, api
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.onchange('mobile')
    def _check_mobile_numeric(self):
        mobile = self.mobile
        if not mobile:
            return {}
        if '+' in mobile and mobile[0] != '+':
            raise ValidationError("Invalid Mobile Number")
        if '+' in mobile and mobile[0] == '+':
            mobile = mobile.replace('+', '')
        mobile = mobile.replace(' ', '')
        if mobile and not mobile.isdigit():
            self.mobile = ''
            raise ValidationError("Invalid Mobile Number")

    @api.onchange('phone')
    def _check_phone_numeric(self):
        phone = self.phone
        if not phone:
            return {}
        if '+' in phone and phone[0] != '+':
            raise ValidationError("Invalid Phone Number")
        if '+' in phone and phone[0] == '+':
            phone = phone.replace('+', '')
        phone = phone.replace(' ', '')
        if phone and not phone.isdigit():
            self.phone = ''
            raise ValidationError("Invalid Phone Number")
