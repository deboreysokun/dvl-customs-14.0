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


class SaleQuotation(models.Model):
    _inherit = "sale.quotation"

    quotation_type = fields.Selection(selection =[
            ('normal', 'Normal'),
            ('logistic', 'Logistic')],
            tracking=True, default='logistic')

    @api.depends('sale_quotation_line_ids.container_20_price', 'sale_quotation_line_ids.container_40_price', 'sale_quotation_line_ids.container_lcl',
    'sale_quotation_line_ids.price_subtotal', 'quotation_type')
    def _compute_total_amount(self):
        for order in self:
            res = super(SaleQuotation, self)._compute_total_amount()
            amount_total = 0.0
            if order.quotation_type == 'normal':
                for line in order.sale_quotation_line_ids:
                    amount_total += line.price_subtotal
                order.update({
                    'total_amount': amount_total,
                })
        return res

    def action_preview_quotation(self):
        self.ensure_one()
        if self.quotation_type == 'logistic':
            return {
                'name': 'Preview Sales Quotation',
                'type': 'ir.actions.report',
                'report_type': 'qweb-html',
                'report_name': 'devel_logistic_management.report_preview_sale_quotation',
                'report_file': 'devel_logistic_management.report_preview_document',
            }
        else:
            return {
                'name': 'Preview Sales Quotation',
                'type': 'ir.actions.report',
                'report_type': 'qweb-html',
                'report_name': 'devel_other_operation.report_preview_sale_normal_quotation',
                'report_file': 'devel_other_operation.report_sale_normal_quotation',
            }

    def _get_name(self):
        record = self
        name = record.name or ''
        if self._context.get('show_quotation_type') and record.quotation_type:
            name = name + " - " + record.quotation_type
        if self._context.get('show_customer') and record.partner_id:
            name = name + " - " + record.partner_id.name
        return name

    def name_get(self):
        res = []
        for record in self:
            name = record._get_name()
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += ["|", "|", ("name", operator, name), ("quotation_type", operator, name), ("partner_id.name", operator, name),]
        return self.search(domain, limit=limit).name_get()

class SaleQuotationLine(models.Model):
    _inherit = "sale.quotation.line"

    qty = fields.Float(default=1.0, tracking=True, string="QTY")
    price_unit = fields.Float(string="Unit price",tracking=True)
    price_subtotal = fields.Float(string="Sub Total",store=True, compute="_compute_price_subtotal",tracking=True, copy=False)

    @api.depends('qty', 'price_unit')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.qty


class SaleQuotationTemplate(models.Model):
    _inherit = "sale.quotation.template"

    template_type = fields.Selection(selection =[
        ('normal', 'Normal'),
        ('logistic', 'Logistic')],
        tracking=True, default='logistic')


class SaleQuotationTemplateLine(models.Model):
    _inherit = "sale.quotation.template.line"

    qty = fields.Float(default=1.0, tracking=True, string="QTY")
    price_unit = fields.Float(string="Unit price",tracking=True)
