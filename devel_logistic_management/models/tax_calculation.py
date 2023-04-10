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

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


class TaxCalculation(models.Model):
    _name = "tax.calculation"
    _order = "date desc, id desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Tax Calculation"
    _check_company_auto = True

    company_id = fields.Many2one(comodel_name='res.company', string='Company',
                                default=lambda self: self.env.company)

    active = fields.Boolean('Active', default=True, tracking=True)
    name = fields.Char(default=lambda self: _('New'),
                copy=False, readonly=True)
    state= fields.Selection(selection =[
        ('draft', 'Draft'),
        ('to_confirm', 'To Confirm'),
        ('done', 'Confirmed')],
        string='State', tracking=True, default="draft")
    description = fields.Char(string='Description')
    date = fields.Date(string='Date', default=fields.Date.context_today)
    operation_type = fields.Selection(selection =[
                    ('import', 'Import'),
                    ('export', 'Export')],
                    string='Type', tracking=True)
    verify_user_id = fields.Many2one('res.users', 'Confirmed by',tracking=True, required=True,
        help='Person responsible for validating this check tax.')
    verify_date = fields.Date('Confirmed Date',tracking=True, readonly=True)

    line_ids = fields.One2many('tax.calculation.line', 'tax_calculation_id', 'Line items')

    shipment_count = fields.Integer(compute='_compute_shipment_count', string='Shipment Count')
    is_editable = fields.Boolean(default=True ,help="Technical field to restrict editing.")

    def _compute_shipment_count(self):
        for record in self:
            shipments = self.env['operation.shipment'].search([
                ('tax_calculation_id', '=', self.id)])
            record.shipment_count = len(shipments)

    def action_view_operation_shipment(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("devel_logistic_management.action_dvl_operation_all")
        action['domain'] = [
            ('tax_calculation_id', '=', self.id)
        ]
        return action

    def action_to_confirm(self):
        if any(record.state != 'draft' for record in self):
            raise UserError(_('Check Tax must be in "Draft" status!'))
        for record in self:
            record.activity_schedule(
                'mail.mail_activity_data_todo', fields.Date.to_string(date.today()),
                _("%s assigned you to verify and confirm this check tax.", self.env.uid),
                user_id=record.verify_user_id.id or self.env.uid)
        self.write({'state': 'to_confirm'})
        return True

    def action_confirm(self):
        if any(record.state != 'to_confirm' for record in self):
            raise UserError(_('Cannot confirm this check tax, because it is not in To Confirm Status!'))
        self.write({'state': 'done', 'verify_user_id': self.env.uid, 'is_editable': False,
           'verify_date': fields.Date.to_string(date.today())
        })
        return True

    def action_draft(self):
        self.write({'state': 'draft', 'verify_date': False, 'is_editable': True})
        return True

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('new')) == _('new'):
            vals['name'] = self.env['ir.sequence'].next_by_code('tax.calculation') or _('new')
        result = super(TaxCalculation, self).create(vals)
        return result

    def unlink(self):
        for record in self:
            raise UserError(_('You can not delete this record. Please archive it instead.'))
        return super(TaxCalculation, self).unlink()

class TaxCalculationLine(models.Model):
    _name = "tax.calculation.line"
    _description = "Tax Calculation Line"
    _check_company_auto = True

    active = fields.Boolean('Active', related='tax_calculation_id.active', tracking=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
            default=lambda self: self.env.company)
    tax_calculation_id = fields.Many2one(comodel_name='tax.calculation', string="Calculation Id", ondelete='cascade', tracking=True,)
    kh_name = fields.Char('Name of Goods in Khmer ', copy=False, tracking=True)
    name = fields.Char('Name of Goods in English', copy=False, tracking=True)
    hs_code_id = fields.Many2one(comodel_name='hs.code', ondelete='cascade', tracking=True)
    remark_hs_code = fields.Char(string="Remark HS Code", tracking=True)
    qty = fields.Float('Quantity', default=1, required=True, tracking=True)
    uom_id = fields.Many2one('uom.unit', tracking=True)
    price_unit = fields.Float('Price', required=True, tracking=True)
    price_subtotal = fields.Float('Amount', compute='_compute_price_subtotal', store=True, tracking=True)
    fta_rate = fields.Float(string="FTA %", help='Free Trade Agreement', tracking=True)
    tax_rate = fields.Float(string="Tax Rate %", help='Total Tax Rate before apply CO form', compute='_compute_tax_rate', store=True, tracking=True)
    tax_rate_co = fields.Float(string="Tax Rate CO %", help='Total Tax Rate after apply CO form', compute='_compute_tax_rate', store=True, tracking=True)
    tax_amount = fields.Float(help='Total Tax Amount before apply CO form', digits='Product Price', compute='_compute_tax_rate', store=True, tracking=True)
    tax_amount_co = fields.Float(help='Total Tax Amount after apply CO form', digits='Product Price', compute='_compute_tax_rate', store=True, tracking=True)
    tariff = fields.Char(compute='_compute_tariff', store=True, tracking=True)
    number = fields.Char(help='The number in HS Code book.', tracking=True)
    ministry_info = fields.Text(related='hs_code_id.ministry_info',string="Ministry", tracking=True)
    new_tax_rate = fields.Char('New Tax Rate?',copy=False, tracking=True, help='to re-calculate tax rate%')
    is_editable = fields.Boolean(default=True ,help="Technical field to restrict editing.")

    @api.depends('hs_code_id', 'hs_code_id.cd', 'hs_code_id.st', 'hs_code_id.vat',
                'hs_code_id.et', 'hs_code_id.at', 'tax_calculation_id.operation_type')
    def _compute_tariff(self):
        for tax in self:
            if tax.tax_calculation_id.operation_type == 'export':
                for line in self:
                    line.tariff = '%s + %s + %s + %s' % (line.hs_code_id.cd, line.hs_code_id.st, line.hs_code_id.vat, line.hs_code_id.et)
            else:
                for line in self:
                    if line.hs_code_id.at != 0:
                        line.tariff = '%s + %s + %s + %s' % (line.hs_code_id.cd, line.hs_code_id.at, line.hs_code_id.st, line.hs_code_id.vat)
                    else:
                        line.tariff = '%s + %s + %s' % (line.hs_code_id.cd, line.hs_code_id.st, line.hs_code_id.vat)

    @api.depends('price_unit', 'qty')
    def _compute_price_subtotal(self):
        for line in self:
            line.price_subtotal = line.price_unit * line.qty

    @api.depends('hs_code_id', 'hs_code_id.cd', 'hs_code_id.st', 'hs_code_id.vat',
                'hs_code_id.et', 'hs_code_id.at', 'fta_rate', 'price_subtotal',
                'tax_calculation_id.operation_type', 'new_tax_rate')
    @api.onchange('new_tax_rate')
    def _compute_tax_rate(self):
        for line in self:
            if line.tax_calculation_id.operation_type == 'import':
                cd = float(line.hs_code_id.cd) / 100 # CD = Customs Tax
                st = float(line.hs_code_id.st) / 100 # ST = Special Tax
                vat = float(line.hs_code_id.vat) / 100 # VAT = Value Added Tax
                #et = float(line.hs_code_id.et) / 100 # ET = Export Tax
                at = float(line.hs_code_id.at) # AT = Additional Tax

                if line.new_tax_rate and float(line.new_tax_rate) == 0:
                    line.tax_rate_co = line.fta_rate
                    line.tax_amount = 0
                    line.tax_amount_co = (line.price_subtotal * float(line.tax_rate_co)) / 100

                elif line.new_tax_rate and float(line.new_tax_rate) != 0 :
                    line.tax_rate_co = float(line.new_tax_rate) - (float(line.hs_code_id.cd) - line.fta_rate)
                    line.tax_amount = (line.price_subtotal * float(line.new_tax_rate)) / 100
                    line.tax_amount_co = (line.price_subtotal * float(line.tax_rate_co)) / 100

                else:
                    line.tax_rate = ((1+cd)*(1+st)*(1+vat)-1) * 100
                    line.tax_rate_co = line.tax_rate - (float(line.hs_code_id.cd) - line.fta_rate)
                    line.tax_amount = (line.price_subtotal*(1+cd)+(line.qty*at))*(1+st)*(1+vat) - line.price_subtotal
                    line.tax_amount_co = (line.price_subtotal*(1+cd)+(line.qty*at))*(1+st)*(1+vat) - line.price_subtotal * (1+(cd-(line.fta_rate/100)))
            else:
                line.tax_rate = 0.0
                line.tax_rate_co = 0.0
                line.tax_amount = 0.0
                line.tax_amount_co = 0.0

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class Import(models.TransientModel):
    _inherit = 'base_import.import'

    @api.model
    def _convert_import_data(self, fields, options):
        data,fields=super(Import,self)._convert_import_data(fields,options)
        if self._context.get('import_tax_line_item'):
            import_field = options.get('import_field')
            tax_calculation_id = options.get('tax_calculation_id')
            if import_field and tax_calculation_id:
                fields.append(import_field)
                for row in data:
                    row.append(tax_calculation_id)
        return data,fields

    def do(self, fields, columns, options, dryrun=False):
        return super(Import,self.with_context(dryrun=dryrun,import_tax_line_item=options.get('import_tax_line_item'))).do(fields,columns,options,dryrun)
