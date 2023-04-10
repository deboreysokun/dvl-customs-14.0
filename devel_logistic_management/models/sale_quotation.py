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
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError


class SaleQuotation(models.Model):
    _name = "sale.quotation"
    _order = "name desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sales Quotation"
    _check_company_auto = True

    company_id = fields.Many2one(comodel_name='res.company', string='Company',
        default=lambda self: self.env.company)
    active = fields.Boolean('Active', default=True, tracking=True)

    name = fields.Char(default=lambda self: _('New'),
            copy=False, readonly=True, string="Quotation No")
    partner_company_id = fields.Many2one('res.partner', string="Company" ,tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer" ,tracking=True)

    att_partner_id = fields.Many2one('res.partner', string="ATT" ,tracking=True)

    issued_quotation_id = fields.Many2one('res.partner', string="Issued By Company" ,tracking=True)
    quotation_date = fields.Date(default=fields.Date.context_today,tracking=True)
    validity_date = fields.Date(tracking=True)
    commodity = fields.Char(tracking=True)
    duty_type = fields.Char(tracking=True)
    service_type = fields.Char(tracking=True)
    sale_user_id = fields.Many2one('res.users', compute_sudo=True, store=True, tracking=True)
    price_user_id = fields.Many2one('res.users', compute_sudo=True, tracking=True, store=True)
    duty_tax_payment = fields.Char(tracking=True)
    payment_term = fields.Char(tracking=True)
    pick_up_location = fields.Char(tracking=True)
    place_of_delivery = fields.Char(tracking= True)
    port_gate = fields.Char(tracking= True)

    template_id = fields.Many2one('sale.quotation.template', tracking= True)
    sale_quotation_line_ids = fields.One2many('sale.quotation.line', 'sale_quotation_id', copy=True)
    note = fields.Text('Terms and conditions', translate=True)
    is_editable = fields.Boolean(default=True ,help="Technical field to restrict editing.")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed')], string='Status', default='draft',
        store=True, tracking=True, copy=False, readonly=True)

    total_amount = fields.Monetary(currency_field='company_currency_id', store=True, readonly=True, compute='_compute_total_amount', tracking=5)
    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related='company_id.currency_id')

    @api.depends('sale_quotation_line_ids.container_20_price', 'sale_quotation_line_ids.container_40_price', 'sale_quotation_line_ids.container_lcl')
    def _compute_total_amount(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_total = 0.0
            for line in order.sale_quotation_line_ids:
                amount_total += line.container_20_price
                amount_total += line.container_40_price
                amount_total += line.container_lcl
            order.update({
                'total_amount': amount_total,
            })

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.quotation') or _('New')
        result = super(SaleQuotation, self).create(vals)
        return result

    @api.onchange('template_id')
    def onchange_template_id(self):
        template_lines = [(5, 0, 0)]
        for line in self.template_id.sale_quotation_template_line_ids:
            data = {
                'sequence': line.sequence,
                'display_type': line.display_type,
                'name': line.name,
                'uom_id': line.uom_id.id,
                'container_20_price': line.container_20_price,
                'container_40_price': line.container_40_price,
                'container_lcl': line.container_lcl,
                'remark': line.remark,
            }
            template_lines.append((0, 0, data))
        self.sale_quotation_line_ids = template_lines
        self.note = self.template_id.note

    def action_confirm(self):
        for record in self:
            record.write({'state': 'confirm', 'is_editable': False})
        return True

    def action_draft(self):
        for record in self:
            record.write({'state': 'draft', 'is_editable': True})
        return True

    def unlink(self):
        for order in self:
            if order.state == 'confirm':
                raise UserError(_('You can not delete a confirmed Sales Quotation. You must set it to draft state first.'))
        return super(SaleQuotation, self).unlink()

    def action_preview_quotation(self):
        self.ensure_one()
        return {
            'name': 'Preview Sales Quotation',
            'type': 'ir.actions.report',
            'report_type': 'qweb-html',
            'report_name': 'devel_logistic_management.report_preview_sale_quotation',
            'report_file': 'devel_logistic_management.report_preview_document',
            'res_model': 'operation.shipment',
        }

class SaleQuotationLine(models.Model):
    _name = "sale.quotation.line"
    _order = 'sale_quotation_id, sequence, id'
    _description = "Sales Quotation Line"

    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of lines.",default=10)
    sale_quotation_id = fields.Many2one('sale.quotation', 'Reference', required=True,
        ondelete='cascade', index=True)
    name = fields.Char('Description', required=True, translate=True, tracking=True)
    remark = fields.Char(tracking=True)
    uom_id = fields.Many2one('uom.unit', string="UOM")
    container_20_price = fields.Float(required=True, tracking=True)
    container_40_price = fields.Float(required=True, tracking=True)
    container_lcl = fields.Float(required=True, tracking=True)
    display_type = fields.Selection([
    ('line_section', "Section"),
    ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    is_editable = fields.Boolean(related="sale_quotation_id.is_editable",store=True,help="Technical field to restrict editing.")

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def unlink(self):
        for line in self:
            if line.sale_quotation_id.state == 'confirm':
                raise UserError(_('You can not delete a confirmed Sales Quotation Line. You must set it to draft state first.'))
        return super(SaleQuotationLine, self).unlink()


class SaleQuotationTemplate(models.Model):
    _name = "sale.quotation.template"
    _description = "Sales Quotation Template"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    company_id = fields.Many2one(comodel_name='res.company', string='Company',
        default=lambda self: self.env.company)

    name = fields.Char(tracking=True,required=True)
    sale_quotation_template_line_ids = fields.One2many('sale.quotation.template.line', 'sale_quotation_template_id', copy=True)
    note = fields.Text('Terms and conditions', translate=True)


class SaleQuotationTemplateLine(models.Model):
    _name = "sale.quotation.template.line"
    _description = "Sales Quotation Template Line"

    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of lines.",default=10)
    sale_quotation_template_id = fields.Many2one('sale.quotation.template', 'Template Reference', required=True,
        ondelete='cascade', index=True)
    name = fields.Char('Description', required=True, translate=True, tracking=True)
    remark = fields.Char(tracking=True)
    uom_id = fields.Many2one('uom.unit', string="UOM")
    container_20_price = fields.Float(required=True, tracking=True)
    container_40_price = fields.Float(required=True, tracking=True)
    container_lcl = fields.Float(required=True, tracking=True)
    display_type = fields.Selection([
    ('line_section', "Section"),
    ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)
