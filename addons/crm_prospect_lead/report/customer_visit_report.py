from odoo import models, api


class CustomerReport(models.AbstractModel):
    _name = 'report.crm_prospect_lead.report_customer_visit'
    _description = 'Customer Visit Report'

    @api.model
    def _get_report_values(self,  docids, data=None):
        ctx = data.get('context')
        active_id = ctx.get('active_id')
        docs = self.env['customer.visit.report'].browse(active_id)
        domain = [('date_of_visit', '>=', docs.from_date),
                  ('date_of_visit', '<=', docs.to_date),
                  ('visited_by_id', 'in', docs.sales_agent_ids.ids),
                  ('customer_id', 'in', docs.customer_ids.ids)
                  ]
        visit_line_ids = self.env['customer.visit.lines'].sudo().search(domain)
        visit_list = []
        for visit in visit_line_ids:
            visit_list.append({
                'serial_no': visit.serial_no,
                'visited_by_id': visit.customer_id,
                'company_id': visit.company_id,
                'address': ' '.join((visit.opportunity_id.street1,
                                     visit.opportunity_id.street2 if visit.opportunity_id.street2 else '',
                                     visit.opportunity_id.city_id.name if visit.opportunity_id.city_id else '',
                                     visit.opportunity_id.state_id.name if visit.opportunity_id.state_id else '',
                                     visit.opportunity_id.country_id.name,
                                     visit.opportunity_id.zip if visit.opportunity_id.zip else '')),

                'contact_name': visit.opportunity_id.contact_name if visit.opportunity_id.contact_name else '',
                'designation': visit.opportunity_id.designation if visit.opportunity_id.designation else '',
                'mobile': visit.opportunity_id.mobile if visit.opportunity_id.mobile else '',
                'email': visit.opportunity_id.email if visit.opportunity_id.email else '',
                'date_of_visit': visit.date_of_visit if visit.date_of_visit else '',
                'time_of_visit': visit.time_of_visit,
                'opportunity_source': visit.opportunity_id.opportunity_source if visit.opportunity_id.opportunity_source else '',
                'user_id': visit.opportunity_id.user_id,
                'next_visit': dict(visit._fields['next_visit'].selection).get(visit.next_visit),
                'next_followup_date': visit.next_followup_date if visit.next_followup_date else '',
                'assign_to_id': visit.assign_to_id,
            })
        data['visit_list'] = visit_list
        return {
            'doc_ids': docs.ids,
            'doc_model': 'customer.visit.report',
            'data': data,
            'docs': docs,
        }
