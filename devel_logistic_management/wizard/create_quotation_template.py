# -*- coding: utf-8 -*-
#############################################################################
#
#    Devel Logistics Co. Ltd
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
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CreateQuotationTemplate(models.TransientModel):
    _name = "create.quotation.template"
    _description = "Create Template from Sale Quotation"

    name = fields.Char(string="Template Name")

    @api.model
    def prepare_lines(self, sequence, display_type, name, uom_id, container_lcl,
        container_20_price, container_40_price, remark):
        return {
            'sequence': sequence,
            'display_type': display_type,
            'name': name,
            'uom_id' : uom_id.id,
            'container_lcl': container_lcl,
            'container_20_price': container_20_price,
            'container_40_price': container_40_price,
            'remark': remark,
        }

    def compute_quotation_line(self, record, lines):
        res = {}
        for line in record.sale_quotation_line_ids:
            lines.append((0, 0, self.prepare_lines(line.sequence, line.display_type, line.name, line.uom_id, line.container_lcl,
                line.container_20_price, line.container_40_price, line.remark)))
        res['lines'] = lines
        return res

    def create_quotation_template(self):
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        for record in records:
            res = self.compute_quotation_line(record, lines)
            vals = {
                'name': self.name,
                'sale_quotation_template_line_ids': res['lines'],
            }
            template_id = self.env['sale.quotation.template'].create(vals)
        return {
            'name': template_id.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.quotation.template',
            'res_id': template_id.id,
        }