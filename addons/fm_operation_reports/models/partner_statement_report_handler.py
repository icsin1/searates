from odoo import models, tools


class PartnerStatementReportHandler(models.AbstractModel):
    _name = 'partner.statement.report.handler'
    _inherit = 'mixin.report.handler'
    _description = 'Partner Statement Report Handler'

    @tools.ormcache('str(record)', 'str(domain)', 'str(kwargs)')
    def _report_handler_partner_statement(self, report, report_line, record, domain, options, **kwargs):

        moves = self.env[report.model_name].sudo().search(domain).mapped('move_id')
        house_containers = moves.house_shipment_ids.sudo().mapped('container_ids')
        container_count = sum(house_containers.mapped('quantity'))
        container_type = False
        payment_status = False

        if not kwargs.get('group_total') and kwargs.get('group_by') == 'id':
            container_type = ','.join(house_containers.mapped('container_type_id.code'))
            payment_status = moves and dict(moves[0]._fields["payment_state"].selection).get(moves[0].payment_state) or ''

        return {
            'container_type': container_type,
            'container_count': container_count,
            'payment_status': payment_status
        }
