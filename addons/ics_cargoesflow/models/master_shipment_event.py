from odoo import models, api


class FreightMasterShipmentEvent(models.Model):
    _inherit = 'freight.master.shipment.event'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super().search(args, offset, limit, order, count)
        # call only if there are ids to show
        if res:
            event_group_by_containers = self.group_by_event_list(res)
            return event_group_by_containers
        return res

    def group_by_event_list(self, res):
        # This method is to group by container number
        event_group_by_containers = self.env['freight.master.shipment.event']
        containers = {}
        if all([each.container_id and each.container_id.id for each in res]):
            for each in res:
                if each.container_id.name not in containers:
                    containers.update({
                            each.container_id.name: each
                        })
                else:
                    containers[each.container_id.name] += each
            for container, event_ids in containers.items():
                event_group_by_containers += event_ids
            return event_group_by_containers
        else:
            return res
