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


class OtherOperationLinePayment(models.TransientModel):
    _name = "other.operation.line.payment"
    _description = "Payment of Other Operation Service"

    payment_date = fields.Date(string="Payment Date", required=True,
        default=fields.Date.context_today)
    amount = fields.Monetary(currency_field='currency_id', compute='_compute_amount')
    communication = fields.Char(string="Memo", store=True, readonly=False,)
    company_id = fields.Many2one('res.company', store=True, copy=False,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
        compute='_compute_currency_id', help="The payment's currency.")
    journal_id = fields.Many2one('account.journal', store=True, readonly=False, compute='_compute_journal_id',
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    company_currency_id = fields.Many2one('res.currency', string="Company Currency",
        related='company_id.currency_id')
    received_user_id = fields.Many2one('res.partner', string='Received By', store=True, readonly=False, compute='_compute_received_user_id')
    source_amount = fields.Monetary(string="Amount to Pay (company currency)", copy=False,
        currency_field='currency_id', compute='_compute_from_lines')

    @api.depends('journal_id')
    def _compute_currency_id(self):
        for wizard in self:
            wizard.currency_id = wizard.journal_id.currency_id or wizard.company_id.currency_id

    @api.depends('company_id')
    def _compute_received_user_id(self):
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))
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
    def prepare_lines(self, account_id, description, sub_total, received_user_id):
        return {
            'account_id': account_id.id,
            'name': description,
            'debit': sub_total > 0 and sub_total or 0.0,
            'credit': sub_total < 0 and -sub_total or 0.0,
            'partner_id': received_user_id.id,
        }

    @api.model
    def compute_expense_line(self, record, lines):
        res = {}
        for line in record:
            lines.append((0, 0, self.prepare_lines
                (line.account_id, line.description, line.sub_total, self.received_user_id)))
        res['lines'] = lines
        return res

    def action_pay_line(self):
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        if any(record.state != 'validate' for record in records):
            raise ValidationError(_('Expense Line must be Approve in order to paid it.'))

        for record in records:
            res = self.compute_expense_line(record, lines)
            vals = {
                'other_service_id': records.other_operation_id.id,
                'narration': self.communication,
                'ref': 'Expense line: ' + records.other_operation_id.name,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'line_ids': res['lines'],
            }
            record.write({
                'state': 'paid',
                'paid_user_id': self.env.user.id,
                'paid_date': self.payment_date,
                'received_user_id': self.received_user_id.id,
                })

        vals['line_ids'].append((0, 0, {
            'name': 'Expense line: ' + records.other_operation_id.name,
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
            '<strong>Expense Lines Entry : <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>') % (
            move_id.id, move_id.name)
        records.other_operation_id.message_post(body=message)
        for record in records:
            record.write({'move_id': move_id.id})
        return True

    def action_direct_payment(self):
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        if any(record.state not in ['draft', 'confirm' , 'validate'] for record in records):
            raise ValidationError(_('Expense Line must be in these status [To Confirm, To Approve, Approved] in order to do the payment'))

        for record in records:
            res = self.compute_expense_line(record, lines)
            vals = {
                'other_service_id': records.other_operation_id.id,
                'narration': self.communication,
                'ref': 'Expense line: ' + records.other_operation_id.name,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'line_ids': res['lines'],
            }
            record.write({
                'state': 'direct_paid',
                'paid_user_id': self.env.user.id,
                'paid_date': self.payment_date,
                'received_user_id': self.received_user_id.id,
                'remark': 'Direct Payment',
                })

        vals['line_ids'].append((0, 0, {
            'name': 'Expense line: ' + records.other_operation_id.name,
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
            '<strong>Expense Lines Entry : <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>') % (
            move_id.id, move_id.name)
        records.other_operation_id.message_post(body=message)
        for record in records:
            record.write({'move_id': move_id.id})
        return True

