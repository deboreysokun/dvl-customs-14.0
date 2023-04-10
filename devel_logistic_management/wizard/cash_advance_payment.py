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
from odoo.exceptions import ValidationError, UserError


class CashAdvancePayment(models.TransientModel):
    _name = "cash.advance.payment"
    _description = "Cash Advance Payment of Operation Shipment"

    def _get_default_advance_remaining_amount(self):
        shipments = self.env['operation.shipment'].browse(self._context.get('active_ids', []))
        context = self._context
        if context.get('remaining_advance_amount'):
            return shipments.total_cash_advance_remaining

    company_id = fields.Many2one('res.company', store=True, copy=False, default=lambda self: self.env.company)
    payment_date = fields.Date(string="Payment Date", required=True, default=fields.Date.context_today)
    amount = fields.Monetary(currency_field='currency_id', compute='_compute_amount')
    communication = fields.Char(string="Memo", store=True, readonly=False,)

    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
        compute='_compute_currency_id', help="The payment's currency.")
    journal_id = fields.Many2one('account.journal', store=True, readonly=False, compute='_compute_journal_id',
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    company_currency_id = fields.Many2one('res.currency', string="Company Currency",
        related='company_id.currency_id')
    received_user_id = fields.Many2one('res.partner', string='Received By', store=True, readonly=False, compute='_compute_received_user_id')
    source_amount = fields.Monetary(string="Amount to Pay (company currency)", copy=False,
        currency_field='currency_id', compute='_compute_from_lines')

    # Clear Remaining Advance
    advance_remaining_amount = fields.Monetary(string="Remaining Amount",currency_field='currency_id', default=_get_default_advance_remaining_amount)
    account_id = fields.Many2one('account.account', store=True, readonly=False,
        domain="[('company_id', '=', company_id), ('deprecated', '=', False), ('is_off_balance', '=', False), ('internal_type', '=', 'other')]",
        help="Debit Account when register cash advance reamaining.")

    @api.depends('journal_id')
    def _compute_currency_id(self):
        for wizard in self:
            wizard.currency_id = wizard.journal_id.currency_id or wizard.company_id.currency_id

    @api.depends('company_id')
    def _compute_received_user_id(self):
        records = self.env['operation.cash.advance'].browse(
            self._context.get('active_ids'))
        for wizard in self:
            if len(records.mapped('received_user_id')) > 1:
                raise ValidationError(_('You cannot pay to different "Receiver" at the same time!'))
            else:
                domain = [('id', 'in', [records.mapped('received_user_id').id])]
                receiver = self.env['res.partner'].search(domain, limit=1)
                wizard.received_user_id = receiver

    @api.depends('company_id')
    def _compute_journal_id(self):
        for wizard in self:
            domain = [
                ('type', 'in', ('bank', 'cash')),
                ('company_id', '=', wizard.company_id.id),
            ]
            journal = self.env['account.journal'].search(domain, limit=1)
            wizard.journal_id = journal

    def _compute_from_lines(self):
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))
        for wizard in self:
            wizard.source_amount = sum(records.mapped('sub_total'))
        return sum(records.mapped('sub_total'))

    @api.depends('source_amount')
    def _compute_amount(self):
        for wizard in self:
            wizard.amount = wizard._compute_from_lines()

    @api.model
    def prepare_lines(self, account_id ,description, sub_total, received_user_id):
        return {
            'account_id': account_id.id,
            'name': description,
            'debit': sub_total > 0 and sub_total or 0.0,
            'credit': sub_total < 0 and -sub_total or 0.0,
            'partner_id': received_user_id.id,
        }

    @api.model
    def compute_advance_line(self, record, lines):
        res = {}
        for line in record:
            lines.append((0, 0, self.prepare_lines
                (line.account_id ,line.description, line.sub_total, line.received_user_id)))
        res['lines'] = lines
        return res

    def action_pay_advance_line(self):
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))

        if any(record.state != 'validate' for record in records):
            raise ValidationError(_('Cash Advance must be Approve in order to Pay it.'))

        for record in records:
            res = self.compute_advance_line(record, lines)
            vals = {
                'shipment_id': records.shipment_id.id,
                'narration': self.communication,
                'ref': 'Cash Advance: ' + records.shipment_id.name,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'line_ids': res['lines'],
            }
            record.write({
                'state': 'paid',
                'advance_user_id': self.env.user.id,
                'advance_date': self.payment_date,
                'received_user_id': self.received_user_id.id,
                })

        vals['line_ids'].append((0, 0, {
            'name': 'Cash Advance: ' + records.shipment_id.name,
            'account_id': self.journal_id.default_account_id.id,
            'journal_id': self.journal_id.id,
            'partner_id': self.received_user_id.id,
            'date': self.payment_date,
            'debit': self.amount < 0.0 and -self.amount or 0.0,
            'credit': self.amount > 0.0 and self.amount or 0.0,
        }))

        move_id = self.env['account.move'].create(vals)
        move_id.post()
        message = _(
            '<strong>Cash Advance Entry : <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>') % (
            move_id.id, move_id.name)
        records.shipment_id.message_post(body=message)
        for record in records:
            record.write({'move_id': move_id.id})
        return True

    # when remaining advance is negative | Advance Paid < Adavance Cleared
    # normal approval proccess. Draft --> Approve --> Paid
    def add_cash_advance_remaining(self):
        shipments = self.env['operation.shipment'].browse(
            self._context.get('active_ids', [])
        )
        if self.advance_remaining_amount == 0.0:
            raise ValidationError(_('Please make sure that Total Amount is not 0.0!'))
        remain_amount = 0
        if self.advance_remaining_amount < 0:
            remain_amount = abs(self.advance_remaining_amount)
        else:
            remain_amount = - self.advance_remaining_amount

        for shipment in shipments:
            cash_advance_line_vals = {
                'shipment_id': shipment.id,
                'account_id': self.account_id.id,
                'description': self.communication,
                'qty': 1.0,
                'unit_price': remain_amount,
                'state': 'draft',
                'requester_user_id': self.env.user.id,
                'request_date': datetime.datetime.today(),
            }
            cash_advance_line = self.env['operation.cash.advance'].create(cash_advance_line_vals)
        return True

    # when remaining advance is positive | Advance Paid > Adavance Cleared
    # No approval process after added to cash advance line, and mark status as paid
    def action_clear_remaining_advance(self):
        shipments = self.env['operation.shipment'].browse(
            self._context.get('active_ids', [])
        )
        if self.advance_remaining_amount == 0.0:
            raise ValidationError(_('Please make sure that Total Amount is not 0.0!'))
        remain_amount = 0
        if self.advance_remaining_amount < 0:
            remain_amount = abs(self.advance_remaining_amount)
        else:
            remain_amount = - self.advance_remaining_amount

        for shipment in shipments:
            debit_vals = {
                'name': 'Clear Remaining Advance: ' + shipments.name,
                'account_id': self.journal_id.default_account_id.id,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'debit': self.advance_remaining_amount > 0.0 and self.advance_remaining_amount or 0.0,
                'credit': self.advance_remaining_amount < 0.0 and -self.advance_remaining_amount or 0.0,
            }
            credit_vals = {
                'name': 'Clear Remaining Advance: ' + shipments.name,
                'account_id': self.account_id.id,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'debit': self.advance_remaining_amount < 0.0 and -self.advance_remaining_amount or 0.0,
                'credit': self.advance_remaining_amount > 0.0 and self.advance_remaining_amount or 0.0,
            }
            vals = {
                'shipment_id': shipment.id,
                'narration': self.communication,
                'ref': 'Clear Remaining Advance: '+ shipments.name,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
            }
            cash_advance_line_vals = {
                'shipment_id': shipment.id,
                'account_id': self.account_id.id,
                'description': self.communication,
                'qty': 1.0,
                'unit_price': remain_amount,
                'state': 'paid',
                'requester_user_id': self.env.user.id,
                'request_date': datetime.datetime.today(),
                'advance_user_id': self.env.user.id,
                'advance_date':  datetime.datetime.now(),
            }
            move = self.env['account.move'].create(vals)
            move.post()
            cash_advance_line = self.env['operation.cash.advance'].create(cash_advance_line_vals)
            cash_advance_line.move_id = move.id
        return True
