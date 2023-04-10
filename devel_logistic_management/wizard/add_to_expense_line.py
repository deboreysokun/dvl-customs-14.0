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


class AddToExpenseLine(models.TransientModel):
    _name = "add.to.expense.line"
    _description = "Feature to add to expense line"

    def _get_default_amount(self):
        shipments = self.env['operation.shipment'].browse(self._context.get('active_ids', []))
        context = self._context
        if context.get('tax_amount'):
            return shipments.total_tax_amount
        if context.get('tax_amount_co'):
            return shipments.total_tax_amount_co

    def _get_default_description(self):
        shipments = self.env['operation.shipment'].browse(self._context.get('active_ids', []))
        if self._context.get('tax_amount'):
            return 'Duty Tax Amount'
        if self._context.get('tax_amount_co'):
            return 'Tax Amount CO'

    def _get_default_account_id(self):
        shipments = self.env['operation.shipment'].browse(self._context.get('active_ids', []))
        if self._context.get('tax_amount') or self._context.get('tax_amount_co') :
            return self.env['account.account'].search([('name', '=', 'Customs Duty Tax')], limit=1)

    account_id = fields.Many2one('account.account', string="Expense Account", default=_get_default_account_id,
        domain="[('company_id', '=', company_id), ('user_type_id', 'in', [15, 17])]",
        help="Expense Line Account")
    amount = fields.Monetary(currency_field='currency_id', default=_get_default_amount)
    qty = fields.Float(string="QTY", default=1.0)
    description = fields.Char(string="Description", default=_get_default_description)
    uom_id = fields.Many2one('uom.unit', string="UOM")
    company_id = fields.Many2one('res.company', store=True, copy=False,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
        related='company_id.currency_id')

    def add_tax_amount(self):
        shipments = self.env['operation.shipment'].browse(
            self._context.get('active_ids', [])
        )
        if self.amount == 0.0:
            raise ValidationError(_('Please make sure that Total Amount is not 0.0!'))

        for shipment in shipments:
            customs_duty_line_vals = {
                'shipment_id': shipment.id,
                'account_id': self.account_id.id,
                'description': self.description,
                'qty': self.qty,
                'unit_price': self.amount / self.qty,
                'duty_tax': True,
                'state': 'draft',
                'requester_user_id': self.env.user.id,
                'requested_date': datetime.datetime.today(),
            }
            customs_duty_line = self.env['shipment.expense.custom.duty'].create(customs_duty_line_vals)
        return True
