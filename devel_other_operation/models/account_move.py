# -*- coding: utf-8 -*-
#############################################################################
#
#    Devel Logistics Co. Ltd - Other Operation App
#
#    Copyrights 2018 Devellog. All Rights Reserved.(<https://devellog.com>)
#    Author: A2A Digital(<https://a2a-digital.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is belonged to Devel Logistics Co. Ltd
#
#############################################################################

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    other_service_id = fields.Many2one('other.operation', string='Other Service Ref.')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    other_service_id = fields.Many2one('other.operation', string="Other Service Ref.", related="move_id.other_service_id", store=True, compute="_compute_other_shipment_id")
    @api.depends('move_id.other_service_id') 
    def _compute_other_shipment_id(self):
        for line in self:
            line.other_service_id = False
            if line.move_id.other_service_id:
                line.other_service_id = line.move_id.other_service_id
            else:
                pass 
