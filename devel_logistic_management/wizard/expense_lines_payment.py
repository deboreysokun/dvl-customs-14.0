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


class ExpenseLinePayment(models.TransientModel):
    _name = "expense.line.payment"
    _description = "Expense Lines of Each Payment"

    payment_date = fields.Date(string="Payment Date", required=True,
        default=fields.Date.context_today)
    amount = fields.Monetary(currency_field='currency_id', compute='_compute_amount')
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
    received_user_id = fields.Many2one('res.partner', string='Received By', store=True, readonly=False, compute='_compute_received_user_id')
    source_amount = fields.Monetary(string="Amount to Pay (company currency)", copy=False,
        currency_field='currency_id', compute='_compute_from_lines')

    # account for clearing cash advance
    account_id = fields.Many2one('account.account', store=True, readonly=False,
        domain="[('company_id', '=', company_id), ('deprecated', '=', False), ('is_off_balance', '=', False), ('internal_type', '=', 'other')]",
        help="Credit Account when clearing cash advance.")

    def _get_group_payment(self):
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))
        shipment_ids = records.mapped('shipment_id')
        if len(shipment_ids) > 1:
            return True
        else:
            return False

    group_payment = fields.Boolean(string="Group Payments", default=_get_group_payment)

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

    def action_pay_expense_line(self):
        record_names = []
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        if any(record.state != 'validate' for record in records):
            raise ValidationError(_('Expense Line must be Approve in order to paid it.'))

        shipment_ids = records.mapped('shipment_id')
        if len(shipment_ids) > 1:
            raise ValidationError(_('You are selecting more than 1 shipment! Please do group payment instead!'))

        for record in records:
            record_names.append(record.description)
            res = self.compute_expense_line(record, lines)
            vals = {
                'shipment_id': records.shipment_id.id,
                'narration': self.communication,
                'ref': 'Expense line: ' + records.shipment_id.name,
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
            'name': 'Expense line: ' + records.shipment_id.name,
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
        records.shipment_id.message_post(body=message)
        for record in records:
            record.write({'move_id': move_id.id})
        return True

    def expense_line_group_payment(self):
        record_names = []
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))
        state = ''
        remark_expense = ''

        if self._context.get('group_direct_payment'):
            if any(record.state not in ['draft', 'confirm' , 'validate'] for record in records):
                raise ValidationError(_('Expense Line must be in these status [To Confirm, To Approve, Approved] in order to do the payment'))
            state = 'direct_paid'
            remark_expense = 'Direct Payment'
        else:
            if any(record.state != 'validate' for record in records):
                raise ValidationError(_('Expense Line must be Approve in order to paid it.'))
            state = 'paid'
            remark_expense = ''

        shipment_ids = records.mapped('shipment_id')
        record_names = [shipment.name for shipment in shipment_ids]

        for shipment in shipment_ids:
            sub_total = 0
            expense_lines = records.filtered(lambda l: l.shipment_id == shipment)
            sub_total = sum(expense_lines.mapped('sub_total'))
            for record in expense_lines:
                res = self.compute_expense_line(record, lines)
                vals = {
                    'narration': self.communication,
                    'ref': 'Expense Group Pay: ' + ", ".join(record_names) ,
                    'journal_id': self.journal_id.id,
                    'date': self.payment_date,
                    'line_ids': res['lines'],
                }
                record.write({
                'state': state,
                'paid_user_id': self.env.user.id,
                'paid_date': self.payment_date,
                'received_user_id': self.received_user_id.id,
                'remark_expense': remark_expense,
                })
            vals['line_ids'].append((0, 0, {
                'shipment_id': shipment.id,
                'name': 'Expense line: ' + shipment.name,
                'account_id': self.journal_id.default_account_id.id,
                'journal_id': self.journal_id.id,
                'partner_id': self.received_user_id.id,
                'date': self.payment_date,
                'debit': sub_total < 0.0 and -sub_total or 0.0,
                'credit': sub_total > 0.0 and sub_total or 0.0,
            }))
        move_id = self.env['account.move'].create(vals)
        move_id.post()
        message = _(
            '<strong>Expense Lines Entry : <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>') % (
            move_id.id, move_id.name)
        for record in records:
            record.write({'move_id': move_id.id})
            record.shipment_id.message_post(body=message)
        return True

    def action_update_recevicer_id(self):
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        if any(record.state != 'draft' for record in records):
            raise ValidationError(_('Expense Line is not in a Draft state! Please reset to Draft first to update records.'))

        for record in records:
            record.write({'received_user_id': self.received_user_id.id})

    # method bypass confirm and approve process
    def action_direct_payment(self):
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))
        if any(record.state not in ['draft', 'confirm' , 'validate'] for record in records):
            raise ValidationError(_('Expense Line must be in these status [To Confirm, To Approve, Approved] in order to do the payment'))

        shipment_ids = records.mapped('shipment_id')
        if len(shipment_ids) > 1:
            raise ValidationError(_('You are selecting more than 1 shipment! Please do group payment instead!'))

        for record in records:
            res = self.compute_expense_line(record, lines)
            vals = {
                'shipment_id': records.shipment_id.id,
                'narration': self.communication,
                'ref': 'Expense line: ' + records.shipment_id.name,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'line_ids': res['lines'],
            }
            record.write({
                'state': 'direct_paid',
                'paid_user_id': self.env.user.id,
                'paid_date': self.payment_date,
                'received_user_id': self.received_user_id.id,
                'remark_expense': 'Direct Payment',
                })

        vals['line_ids'].append((0, 0, {
            'name': 'Expense line: ' + records.shipment_id.name,
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
        records.shipment_id.message_post(body=message)
        for record in records:
            record.write({'move_id': move_id.id})
        return True

    # Clear Cash Advance Remaining
    def action_clear_advance_payment(self):
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))

        if any((record.shipment_id.total_cash_advance_cleared == record.shipment_id.total_cash_advance_paid) and record.shipment_id.total_cash_advance_paid != 0 for record in records):
            raise ValidationError(_('You cannot do clearing cash advance since remaining advance is 0.0!'))

        if any(record.state not in ['draft', 'confirm', 'validate'] for record in records):
            raise ValidationError(_('You can clear this advance only status is "To Confirm", "To Approve", or "Approved".'))

        for record in records:
            res = self.compute_expense_line(record, lines)
            vals = {
                'shipment_id': records.shipment_id.id,
                'narration': self.communication,
                'ref': 'Cleared Cash Advance: ' + records.shipment_id.name,
                'journal_id': self.journal_id.id,
                'date': self.payment_date,
                'line_ids': res['lines'],
            }
            record.write({
                'state': 'paid',
                'paid_user_id': self.env.user.id,
                'paid_date': self.payment_date,
                'received_user_id': self.received_user_id.id,
                'clear_advance': True,
                })

        vals['line_ids'].append((0, 0, {
            'name': 'Clear Cash Advance: ' + records.shipment_id.name,
            'account_id': self.account_id.id,
            'journal_id': self.journal_id.id,
            'partner_id': self.received_user_id.id,
            'date': self.payment_date,
            'debit': self.amount < 0.0 and -self.amount or 0.0,
            'credit': self.amount > 0.0 and self.amount or 0.0,
        }))

        move_id = self.env['account.move'].create(vals)
        move_id.post()
        message = _(
            '<strong>Clear Cash Advance Entry : <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>') % (
            move_id.id, move_id.name)
        records.shipment_id.message_post(body=message)
        for record in records:
            record.write({'move_id': move_id.id})
        return True

class ExpenseLineReject(models.TransientModel):
    _name = "expense.line.reject"
    _description = "Operation Shipment Expense Line Reject Reason"

    reason = fields.Text(string="Reason")

    def action_reject_expense_line(self):
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))

        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to reject this!'))
        if any(request.state != 'confirm' for request in records):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to reject it.'))

        records.filtered(lambda request: request.state == 'confirm').write({
            'state': 'reject',
            'reason': self.reason,
            })
        return True
