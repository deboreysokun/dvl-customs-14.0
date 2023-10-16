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


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.returns('self')
    def _get_default_exchange_currency(self):
        return self.env['res.currency'].search([('name', '=', 'KHR')], limit=1)

    exchange_currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True,
        states={'draft': [('readonly', False)]}, default=_get_default_exchange_currency)


    shipment_id = fields.Many2one('operation.shipment', string='Shipment Ref.')
    exchange_rate = fields.Float('Exchange Rate', store=True, readonly=True, compute="_compute_exchange_rate")
    amount_total_khr = fields.Float(string='Total in', compute='_compute_amount_total_khr')
    # Use to display in invoice header
    company_header_id = fields.Many2one('res.partner', string='Header Invoice')
    agent_staff_id = fields.Many2one('res.partner', string='Agent Staff Name')
    client_company_id = fields.Many2one('res.partner', string='Client of Agent')
    client_staff_id = fields.Many2one('res.partner', string="Staff of Agent's Client")

    # Extra fields on Reimbursement Invoice/Bill
    is_reimbursement_invoice = fields.Boolean()
    print_receipt = fields.Boolean(string="Print Only Receipt")
    print_2digits = fields.Boolean(string="Print 2 Digits",default=False)
    print_3digits = fields.Boolean(string="Print 3 Digits",default=False)

    # Use to input KHQR
    khqr = fields.Many2one('account.khqr', string="KHQR Option")


    @api.depends('exchange_rate')
    def _compute_amount_total_khr(self):
        for move in self:
            move.amount_total_khr = move.currency_id._convert(move.amount_total, move.exchange_currency_id, move.company_id, move.invoice_date or fields.Date.today())

    @api.onchange('amount_total', 'exchange_rate')
    def _onchange_amount_total(self):
        for move in self:
            move.amount_total_khr = move.currency_id._convert(move.amount_total, move.exchange_currency_id, move.company_id, move.invoice_date or fields.Date.today())

    @api.depends('exchange_currency_id')
    def _compute_exchange_rate(self):
        for move in self:
            currency_rates = move.exchange_currency_id._get_rates(move.company_id, move.invoice_date or fields.Date.today())
            move.exchange_rate = currency_rates.get(move.exchange_currency_id.id) or 1.0

    # ==== Invocie Copy From field ====
    invoice_copy_from_id = fields.Many2one('account.move', store=False,
        check_company=True,
        string='Copy From',
        help="Copy line from a past invoice.")

    @api.onchange('invoice_copy_from_id')
    def _onchange_invoice_copy_from_id(self):
        if self.invoice_copy_from_id:
            # Copy invoice lines.
            for line in self.invoice_copy_from_id.invoice_line_ids:
                copied_vals = line.copy_data()[0]
                copied_vals['move_id'] = self.id
                copied_vals['account_id'] = self.journal_id.default_account_id.id
                new_line = self.env['account.move.line'].new(copied_vals)
                new_line.recompute_tax_line = True

            # Copy currency.
            if self.currency_id != self.invoice_copy_from_id.currency_id:
                self.currency_id = self.invoice_copy_from_id.currency_id

            # Reset
            self.invoice_copy_from_id = False
            self._recompute_dynamic_lines()

    commodity = fields.Char(string="Commodity", related="shipment_id.commodity")
    


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _order = "date desc, move_name desc, sequence, id"

    print_2digits = fields.Boolean(string="Print 2 Digits",default=False, compute="_compute_2digits")
    @api.depends('move_id.print_2digits')
    def _compute_2digits(self):
        for line in self:
            line.print_2digits = False
            if line.move_id.print_2digits:
                line.print_2digits = line.move_id.print_2digits
            else:
                pass
    
    print_3digits = fields.Boolean(string="Print 3 Digits",default=False, compute="_compute_3digits")
    @api.depends('move_id.print_3digits')
    def _compute_3digits(self):
        for line in self:
            line.print_3digits = False
            if line.move_id.print_3digits:
                line.print_3digits = line.move_id.print_3digits
            else:
                pass


    shipment_id = fields.Many2one('operation.shipment', string="Shipment Ref.", compute="_compute_shipment_id", readonly=False, store=True)

    # remove domain="[('category_id', '=', product_uom_category_id)]" from this field
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', domain="[]")

    @api.depends('move_id.shipment_id')
    def _compute_shipment_id(self):
        for line in self:
            line.shipment_id = False
            if line.move_id.shipment_id:
                line.shipment_id = line.move_id.shipment_id
            else:
                pass

    # overwrite this methond to aviod recompute price_unit
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if not line.product_id or line.display_type in ('line_section', 'line_note'):
                continue

            line.name = line._get_computed_name()
            line.account_id = line._get_computed_account()
            taxes = line._get_computed_taxes()
            if taxes and line.move_id.fiscal_position_id:
                taxes = line.move_id.fiscal_position_id.map_tax(taxes, partner=line.partner_id)
            line.tax_ids = taxes
            #comment these lines
            #line.product_uom_id = line._get_computed_uom()
            #line.price_unit = line._get_computed_price_unit()

    @api.onchange('product_uom_id')
    def _onchange_uom_id(self):
        ''' Recompute the 'price_unit' depending of the unit of measure. '''
        if self.display_type in ('line_section', 'line_note'):
            return
        taxes = self._get_computed_taxes()
        if taxes and self.move_id.fiscal_position_id:
            taxes = self.move_id.fiscal_position_id.map_tax(taxes, partner=self.partner_id)
        self.tax_ids = taxes
        #comment this line
        #self.price_unit = self._get_computed_price_unit()


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    is_reimbursement = fields.Boolean(string='Is Reimbursement?', help="To Identify Journal that is for Reimbursement for Logistic operation")
