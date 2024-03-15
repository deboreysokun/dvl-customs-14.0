from odoo import models, api, fields

class TransitOperationShipmentReport(models.TransientModel):

    _name = "transit.operation.shipment.report"

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    def action_filter_transit_operations(self):
        
        domain = [('operation_type', '=', 'transit'), ('date', '>=', self.start_date), ('date', '<=', self.end_date)]
        
        return {
            'name': 'Transit Operations',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('devel_logistic_management.view_shipment_operation_tree').id, 'tree'),
                (self.env.ref('devel_logistic_management.view_shipment_operation_form').id, 'form'),
            ],
            'res_model': 'operation.shipment',
            'domain': domain,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }