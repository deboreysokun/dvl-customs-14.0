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
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError

class CreateSalesQuotationFromTemplate(models.TransientModel):
    _name = "create.sale.quotation.wizard"
    _description = "Create Sale Quotation From Template"

    def _get_default_quotation_type(self):
        active_model = self._context.get('active_model')
        records = self.env['sale.quotation.template'].browse(
            self._context.get('active_ids'))
        for record in records:
            return record.template_type

    quotation_type = fields.Selection(selection =[
        ('normal', 'Normal'),
        ('logistic', 'Logistic')],
        tracking=True, default=_get_default_quotation_type)

    @api.model
    def prepare_lines(self, sequence, display_type, name, qty ,uom_id, price_unit,container_lcl,
        container_20_price, container_40_price, remark):
        return {
            'sequence': sequence,
            'display_type': display_type,
            'name': name,
            'qty': qty,
            'uom_id' : uom_id.id,
            'price_unit': price_unit,
            'container_lcl': container_lcl,
            'container_20_price': container_20_price,
            'container_40_price': container_40_price,
            'remark': remark,
        }

    def compute_template_line(self, record, lines):
        res = {}
        for line in record.sale_quotation_template_line_ids:
            lines.append((0, 0, self.prepare_lines(line.sequence, line.display_type, line.name, line.qty ,line.uom_id, line.price_unit, line.container_lcl,
                line.container_20_price, line.container_40_price, line.remark)))
        res['lines'] = lines
        return res

    def create_sales_quotation(self):
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        for record in records:
            res = self.compute_template_line(record, lines)
            vals = {
                'template_id': record.id,
                'quotation_type': self.quotation_type,
                'sale_quotation_line_ids': res['lines'],
            }
            quotation_id = self.env['sale.quotation'].create(vals)
        return {
            'name': quotation_id.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sale.quotation',
            'res_id': quotation_id.id,
        }


class CreateQuotationTemplate(models.TransientModel):
    _inherit = "create.quotation.template"
    ### override action "Create Quotation Template" to include type of template, qty and price unit for normal template

    def _get_default_template_type(self):
        active_model = self._context.get('active_model')
        records = self.env['sale.quotation'].browse(
            self._context.get('active_ids'))
        for record in records:
            return record.quotation_type

    template_type = fields.Selection(selection =[
        ('normal', 'Normal'),
        ('logistic', 'Logistic')],
        tracking=True, default=_get_default_template_type)

    # include qty and price_unit  for type of normal template
    @api.model
    def prepare_lines(self, sequence, display_type, name, qty ,uom_id, price_unit, container_lcl,
        container_20_price, container_40_price, remark):
        return {
            'sequence': sequence,
            'display_type': display_type,
            'name': name,
            'qty': qty,
            'uom_id' : uom_id.id,
            'price_unit': price_unit,
            'container_lcl': container_lcl,
            'container_20_price': container_20_price,
            'container_40_price': container_40_price,
            'remark': remark,
        }

    def compute_quotation_line(self, record, lines):
        res = {}
        for line in record.sale_quotation_line_ids:
            lines.append((0, 0, self.prepare_lines(line.sequence, line.display_type, line.name, line.qty, line.uom_id, line.price_unit,
            line.container_lcl, line.container_20_price, line.container_40_price, line.remark)))
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
                'template_type': self.template_type,
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
