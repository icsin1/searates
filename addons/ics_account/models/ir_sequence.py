from datetime import datetime
import pytz
from odoo import models, fields, _
from odoo.exceptions import UserError


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    def _get_fiscal_year_data(self, date=None):
        company = self.env.company
        date = date or fields.Date.today()
        current_date = fields.Date.from_string(date) if isinstance(date, str) else date
        dates = company.compute_fiscalyear_dates(current_date)

        date_start = fields.Date.from_string(dates.get('date_from'))
        date_end = fields.Date.from_string(dates.get('date_to'))

        start_year = date_start.year
        end_year = date_end.year

        fiscal_year_data = {
            'fys_year': start_year,
            'fys_y': str(start_year)[-2:],
            'fye_year': end_year,
            'fye_y': str(end_year)[-2:]
        }
        return fiscal_year_data

    def _get_prefix_suffix(self, date=None, date_range=None):
        if not date and self.env.context.get('ir_sequence_date'):
            date = self.env.context.get('ir_sequence_date')
        self.ensure_one()
        keys_to_check = ['fys_', 'fye_']
        if not any([bool((self.suffix and key in self.suffix) or (self.prefix and key in self.prefix)) for key in keys_to_check]):
            return super()._get_prefix_suffix(date=date, date_range=date_range)

        """ FIXME: Dharmang Soni, Parth Joshi
            As odoo have code which can't be override or change we need to force rewrite whole method code here.
            In future, if they change or add capability to override plz do the changes in this code accordingly.
        """
        def _interpolate(s, d):
            return (s % d) if s else ''

        def _interpolation_dict():
            now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(date or self._context.get('ir_sequence_date'))
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(date_range or self._context.get('ir_sequence_date_range'))

            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
            }
            res = {}
            for key, format in sequences.items():
                res[key] = effective_date.strftime(format)
                res['range_' + key] = range_date.strftime(format)
                res['current_' + key] = now.strftime(format)

            res.update(**self._get_fiscal_year_data(date=date))

            return res
        d = _interpolation_dict()
        try:
            interpolated_prefix = _interpolate(self.prefix, d)
            interpolated_suffix = _interpolate(self.suffix, d)
        except ValueError:
            raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % self.name)
        return interpolated_prefix, interpolated_suffix
