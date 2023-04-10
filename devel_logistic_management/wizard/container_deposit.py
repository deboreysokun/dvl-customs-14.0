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


class ContainerDeposit(models.TransientModel):
    _name = "container.deposit"
    _description = "Container Deposit of Shipment Operation"

    payment_date = fields.Date(string="Payment Date", required=True,
        default=fields.Date.context_today)
    amount = fields.Monetary(currency_field='currency_id', compute='_compute_amount', readonly=False,store=True)
    communication = fields.Char(string="Memo", store=True, readonly=False,)
    company_id = fields.Many2one('res.company', store=True, copy=False,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
        compute='_compute_currency_id',
        help="The payment's currency.")
    journal_id = fields.Many2one('account.journal', store=True, readonly=False, compute='_compute_journal_id',
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    company_currency_id = fields.Many2one('res.currency', string="Company Currency",
        related='company_id.currency_id')
    account_id = fields.Many2one('account.account', store=True, readonly=False, compute='_compute_account_id',
        domain="[('company_id', '=', company_id), ('user_type_id', '=', 19)]",
        help="Debit Account when Register Deposit. Credit Account when Refund Deposit.")
    refund_deposit_qty = fields.Integer(string="Qty", compute='_compute_amount', readonly=False,store=True,
        help="Deposti QTY when Register Deposit. Refund QTY when Refund Deposit.")
    source_qty = fields.Integer(compute='_compute_from_shipment', readonly=False,)
    source_amount = fields.Monetary(string="Amount to Pay (company currency)", copy=False,
        currency_field='currency_id', compute='_compute_from_shipment')
    # Technical field to calculate the remaining refund deposit container amount in case of multiple refund time
    remaining_refund_amount =  fields.Float(compute='_compute_remaining_amount')

    @api.depends('journal_id')
    def _compute_currency_id(self):
        for wizard in self:
            wizard.currency_id = wizard.journal_id.currency_id or wizard.company_id.currency_id

    @api.depends('company_id')
    def _compute_account_id(self):
        for wizard in self:
            domain = [
                ('user_type_id', '=', 19),
                ('company_id', '=', wizard.company_id.id),
            ]
            account = self.env['account.account'].search(domain, limit=1)
            wizard.account_id = account

    @api.depends('company_id')
    def _compute_journal_id(self):
        for wizard in self:
            domain = [
                ('type', 'in', ('bank', 'cash')),
                ('company_id', '=', wizard.company_id.id),
            ]
            journal = self.env['account.journal'].search(domain, limit=1)
            wizard.journal_id = journal

    @api.depends('company_id')
    def _compute_from_shipment(self):
        shipments = self.env['operation.shipment'].browse(
            self._context.get('active_ids', [])
        )
        for wizard in self:
            wizard.source_amount = shipments.total_deposit_amount
            wizard.source_qty = shipments.total_container_qty
        return wizard.source_amount, wizard.source_qty

    @api.depends('company_id')
    def _compute_remaining_amount(self):
        shipments = self.env['operation.shipment'].browse(
            self._context.get('active_ids', [])
        )
        for wizard in self:
            wizard.remaining_refund_amount = shipments.refund_container_remain_amount


    @api.depends('source_amount', 'source_qty', 'remaining_refund_amount')
    def _compute_amount(self):
        for wizard in self:
            wizard.amount, wizard.refund_deposit_qty = wizard._compute_from_shipment()
            shipments = self.env['operation.shipment'].browse(self._context.get('active_ids', []))
            context = self._context
            if context.get('refund_deposit_container'):
                if wizard.remaining_refund_amount != 0.0 and wizard.remaining_refund_amount < wizard.source_amount:
                    wizard.amount = wizard.remaining_refund_amount
                if wizard.remaining_refund_amount == wizard.source_amount:
                    wizard.amount = 0
                    wizard.source_qty = 0

    # Added Container Deposit Amounts to Shipping Expense Line with To Confirm Status
    def register_container_deposit(self):
        shipments = self.env['operation.shipment'].browse(
            self._context.get('active_ids', [])
        )
        if self.amount == 0.0:
            raise ValidationError(_('Please make sure that Total Amount is not 0.0!'))

        if self.amount > self.source_amount:
            raise ValidationError(_('The current amount is bigger than the original amount!'))

        for shipment in shipments:
            if shipment.container_deposit_qty == 0:
                raise ValidationError(_('Please make sure that Container Qty is not 0!'))

            if shipment.container_deposit_move_id:
                raise ValidationError(_('There is a Journal Entry linked to this deposit already.'))
            else:
                debit_vals = {
                    'name': 'Deposit Containers: ' + shipments.name,
                    'account_id': self.account_id.id,
                    'journal_id': self.journal_id.id,
                    'date': self.payment_date,
                    'debit': self.amount > 0.0 and self.amount or 0.0,
                    'credit': self.amount < 0.0 and -self.amount or 0.0,
                }
                credit_vals = {
                    'name': 'Deposit Containers: ' + shipments.name,
                    'account_id': self.journal_id.default_account_id.id,
                    'journal_id': self.journal_id.id,
                    'date': self.payment_date,
                    'debit': self.amount < 0.0 and -self.amount or 0.0,
                    'credit': self.amount > 0.0 and self.amount or 0.0,
                }
                vals = {
                    'shipment_id': shipment.id,
                    'narration': self.communication,
                    'ref': 'Deposit Containers: '+  shipments.name,
                    'journal_id': self.journal_id.id,
                    'date': self.payment_date,
                    'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
                }
                shipping_line_vals = {
                    'shipment_id': shipment.id,
                    'account_id': self.account_id.id,
                    'description': 'Deposit Containers',
                    'qty': self.refund_deposit_qty, # Contatienr QTY To Deposit
                    'unit_price': self.amount / self.refund_deposit_qty,
                    'state': 'draft',
                    'requester_user_id': self.env.user.id,
                    'requested_date': datetime.datetime.today(),
                }
                shipping_line = self.env['shipment.expense.shipping.line'].create(shipping_line_vals)
                shipment.container_deposit_date = datetime.datetime.today()
        return True

    # Added Refund Container Deposit Amounts to Shipping Expense Line with Paid Status
    def refund_deposit_container(self):
        shipments = self.env['operation.shipment'].browse(
            self._context.get('active_ids', [])
        )
        if self.amount == 0.0:
            raise ValidationError(_('Please make sure that Total Amount is not 0.0!'))

        if self.refund_deposit_qty == 0:
            raise ValidationError(_('Please make sure that Refund Qty is not 0.0!'))

        if self.source_amount == self.remaining_refund_amount:
            raise ValidationError(_('Total Deposit Container and Total Refund Deposit Container are equal!'))

        if self.amount > self.source_amount or (self.amount > self.remaining_refund_amount and self.remaining_refund_amount != 0):
            raise ValidationError(_('You cannot register amount that is bigger that the deposit amount or remaining amount!'))

        for shipment in shipments:
            debit_vals = {
                'name': 'Refund Deposit Containers: ' + shipments.name,
                'account_id': self.journal_id.default_account_id.id,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'debit': self.amount > 0.0 and self.amount or 0.0,
                'credit': self.amount < 0.0 and -self.amount or 0.0,
            }
            credit_vals = {
                'name': 'Refund Deposit Containers: ' + shipments.name,
                'account_id': self.account_id.id,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'debit': self.amount < 0.0 and -self.amount or 0.0,
                'credit': self.amount > 0.0 and self.amount or 0.0,
            }
            vals = {
                'shipment_id': shipment.id,
                'narration': self.communication,
                'ref': 'Refund Deposit Containers: '+ shipments.name,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            shipping_line_vals = {
                'shipment_id': shipment.id,
                'account_id': self.account_id.id,
                'description': 'Refund Deposit Containers',
                'qty': self.refund_deposit_qty, # Contatienr QTY To Refund
                'unit_price': - (self.amount / self.refund_deposit_qty),
                'state': 'paid',
                'requester_user_id': self.env.user.id,
                'paid_user_id': self.env.user.id,
                'paid_date': self.payment_date,
            }
            move = self.env['account.move'].create(vals)
            move.post()
            shipping_line = self.env['shipment.expense.shipping.line'].create(shipping_line_vals)
            shipping_line.move_id = move.id
            shipment.refund_container_deposit_date = move.date
            shipment.refund_container_deposit_move_ids += move
            shipment.refund_container_deposit_qty += self.refund_deposit_qty
            if shipment.refund_container_deposit_qty > shipment.container_deposit_qty:
                shipment.refund_container_deposit_qty = shipment.container_deposit_qty
        return True
