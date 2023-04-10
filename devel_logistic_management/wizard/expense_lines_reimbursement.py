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


class ExpenseLineReimbursement(models.TransientModel):
    _name = "expense.line.reimbursement"
    _description = "Expense Lines Reimbursement"

    amount = fields.Monetary(currency_field='currency_id', compute='_compute_amount')
    communication = fields.Char(string="Memo", store=True, readonly=False,)
    company_id = fields.Many2one('res.company', store=True, copy=False,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
        compute='_compute_currency_id',
        help="The payment's currency.")
    company_currency_id = fields.Many2one('res.currency', string="Company Currency",
        related='company_id.currency_id')
    received_user_id = fields.Many2one('res.partner', string='Received By', store=True, readonly=False, compute='_compute_received_user_id')
    source_amount = fields.Monetary(string="Amount to Pay (company currency)", copy=False,
        currency_field='currency_id', compute='_compute_from_lines')

    reimburse_journal_id = fields.Many2one('account.journal', store=True, readonly=False, compute='_compute_reimburse_journal_id',
        domain="[('company_id', '=', company_id), ('is_reimbursement', '=', True)]")
    client_id = fields.Many2one('res.partner', string='Reimbursed To', store=True, readonly=False, compute='_compute_client_id')

    amount_in_bank_slip = fields.Monetary(currency_field='currency_id', string="Bank Slip Amount")
    journal_id = fields.Many2one('account.journal', store=True, readonly=False, compute='_compute_journal_id',
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    payment_date = fields.Date(string="Payment Date", required=True, default=fields.Date.context_today)
    received_bank_slip = fields.Boolean(string="Received Bank Slip?", defalut=False, store=True, readonly=False, compute="_compute_received_bank_slip" )
    exchange_rate = fields.Float(default=1.0)

    #update to existing reimbursement invoice
    reimburse_invoice_id = fields.Many2one('account.move', domain="[('state', '=', 'draft'),('move_type', 'in', ('out_invoice', 'in_invoice')), ('journal_id.is_reimbursement', '=', True), ('shipment_id', '=', shipment_id)]")
    shipment_id = fields.Many2one('operation.shipment', store=True, readonly=False, compute="_compute_reimburse_shipment_id")

    @api.depends('company_id')
    def _compute_reimburse_shipment_id(self):
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))
        for wizard in self:
            domain = [('id', 'in', [records.mapped('shipment_id').id])]
            wizard.shipment_id = self.env['operation.shipment'].search(domain, limit=1)

    @api.depends('company_id')
    def _compute_currency_id(self):
        for wizard in self:
            wizard.currency_id = wizard.reimburse_journal_id.currency_id or wizard.company_id.currency_id

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

    @api.depends('company_id')
    def _compute_reimburse_journal_id(self):
        for wizard in self:
            domain = [
                ('is_reimbursement', '=', True),
                ('company_id', '=', wizard.company_id.id),
            ]
            journal = self.env['account.journal'].search(domain, limit=1)
            wizard.reimburse_journal_id = journal

    def _compute_from_lines(self):
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))
        for wizard in self:
            wizard.source_amount = abs(sum(records.mapped('sub_total')))
        return abs(sum(records.mapped('sub_total')))

    @api.depends('source_amount')
    def _compute_amount(self):
        for wizard in self:
            wizard.amount = wizard._compute_from_lines()

    @api.depends('currency_id', 'exchange_rate', 'received_bank_slip')
    @api.onchange('currency_id', 'exchange_rate', 'received_bank_slip')
    def _onchange_currency_id(self):
        for wizard in self:
            if wizard.currency_id != wizard.company_currency_id:
                wizard.amount = wizard._compute_from_lines() * wizard.exchange_rate
            else:
                wizard.amount = wizard._compute_from_lines() * 1
            wizard.amount_in_bank_slip = 0

    @api.depends('company_id')
    def _compute_client_id(self):
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))
        for wizard in self:
            domain = [('id', '=', records.shipment_id.customer_id.id)]
            client = self.env['res.partner'].search(domain, limit=1)
            wizard.client_id = client

    @api.depends('reimburse_journal_id')
    def _compute_received_bank_slip(self):
        for wizard in self:
            wizard.received_bank_slip = False
            wizard.amount_in_bank_slip = 0.0

    @api.model
    def prepare_invoice_reimburse_line(self, account_id, description, unit_price, qty, uom_id, currency_id):
        default_uom_id = self.env['uom.uom'].search([('id', '=', 1)]) # Units
        uom_line_id = self.env['uom.uom'].search([('name', '=', uom_id.name)], limit=1)
        if self.reimburse_journal_id.type == 'sale':
            return {
                'account_id': account_id.id,
                'name': description or account_id.name,
                'price_unit': abs(unit_price),
                'quantity': qty,
                'product_uom_id': uom_line_id or default_uom_id,
                'currency_id': currency_id.id,
            }
        else:
            return {
                'account_id': account_id.id,
                'name': description or account_id.name,
                'price_unit': - unit_price,
                'quantity': qty,
                'product_uom_id': uom_line_id or default_uom_id,
                'currency_id': currency_id.id,
            }

    @api.model
    def compute_invoice_reimburse_line(self, record, lines):
        res = {}
        reimburse_line = record.filtered(lambda l: l.account_id.user_type_id.id != 19)
        for line in reimburse_line:
            lines.append((0, 0, self.prepare_invoice_reimburse_line
                (line.account_id, line.description, abs(line.unit_price), line.qty, line.uom_id  ,line.currency_id)))
        res['lines'] = lines
        return res

    @api.model
    def _create_bank_slip_entry(self):
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))
        balance = self.currency_id._convert(abs(self.amount_in_bank_slip), self.company_currency_id, self.company_id, self.payment_date)
        debit_vals = {
            'name': 'Bank Slip',
            'account_id': self.journal_id.default_account_id.id,
            'journal_id': self.journal_id.id,
            'currency_id' : self.currency_id.id,
            'date': self.payment_date,
            'amount_currency': abs(self.amount_in_bank_slip),
            'debit': balance > 0.0 and balance or 0.0,
            'credit': 0.0,

        }
        credit_vals = {
            'name': 'Bank Slip',
            'account_id': self.reimburse_journal_id.default_account_id.id,
            'journal_id': self.journal_id.id,
            'currency_id' : self.currency_id.id,
            'date': self.payment_date,
            'amount_currency': - abs(self.amount_in_bank_slip),
            'debit': 0.0,
            'credit': balance > 0.0 and balance or 0.0,
        }
        vals = {
            'shipment_id': records.shipment_id.id,
            'ref': 'Bank Slip',
            'journal_id': self.journal_id.id,
            'currency_id' : self.currency_id.id,
            'date': self.payment_date,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        move = self.env['account.move'].create(vals)
        move.post()
        return True


    def action_reimburse_expense_line(self):
        record_names = []
        lines = []
        move_type = ''
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))

        if any(record.state not in ['paid', 'direct_paid'] for record in records):
            raise ValidationError(_('Expense Line must paid in order to do Reimbursement!'))

        if self.reimburse_journal_id.type == 'sale':
            move_type = 'out_invoice'
        else:
            move_type = 'in_invoice'

        for record in records:
            record_names.append(record.description)
            res = self.compute_invoice_reimburse_line(record, lines)
            vals = {
                'partner_id': self.client_id.id,
                'shipment_id': records.shipment_id.id,
                'journal_id': self.reimburse_journal_id.id,
                'currency_id': self.currency_id.id,
                'move_type': move_type,
                'invoice_line_ids': res['lines'],
            }
            record.write({
                'state': 'reimbursed',
                'sub_total': 0,
            })
        if self.amount_in_bank_slip != 0.0 and self.reimburse_journal_id.type == 'sale':
            vals['invoice_line_ids'].append((0, 0, {
                'account_id': self.reimburse_journal_id.default_account_id.id,
                'name': 'Bank Slip',
                'price_unit': - abs(self.amount_in_bank_slip),
                'quantity': 1.0,
                'currency_id': self.currency_id.id,
            }))
            self._create_bank_slip_entry()

        if self.amount_in_bank_slip != 0.0 and self.reimburse_journal_id.type == 'purchase':
            vals['invoice_line_ids'].append((0, 0, {
            'account_id': self.reimburse_journal_id.default_account_id.id,
            'name': 'Bank Slip',
            'price_unit': abs(self.amount_in_bank_slip),
            'quantity': 1.0,
            'currency_id': self.currency_id.id,
            }))
            self._create_bank_slip_entry()

        if self.reimburse_invoice_id:
            self.reimburse_invoice_id.write({
                'invoice_line_ids': vals['invoice_line_ids'],
            })
        else:
            invoice_reimbursment_id = self.env['account.move'].create(vals)
            message = _(
                '<strong>Reimbursement Entry : <a href=# data-oe-model=account.move data-oe-id=%d>%s</a>') % (
                invoice_reimbursment_id.id, invoice_reimbursment_id.name)
            records.shipment_id.message_post(body=message)
        return True



class CreateBankSlipEntry(models.TransientModel):
    _name = "create.bank.slip.entry"
    _description = "Action Create Bank Slip On Invoice"

    amount = fields.Monetary(currency_field='currency_id', compute='_compute_amount')
    company_id = fields.Many2one('res.company', store=True, copy=False,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', store=True, readonly=False,
        compute='_compute_currency_id',
        help="The payment's currency.")
    company_currency_id = fields.Many2one('res.currency', string="Company Currency",
        related='company_id.currency_id')

    amount_in_bank_slip = fields.Monetary(currency_field='currency_id', string="Bank Slip Amount")
    payment_journal_id = fields.Many2one('account.journal', store=True, readonly=False, compute='_compute_payment_journal_id',
        domain="[('company_id', '=', company_id), ('type', 'in', ('bank', 'cash'))]")
    payment_date = fields.Date(string="Payment Date", required=True, default=fields.Date.context_today)

    @api.depends('company_id')
    def _compute_currency_id(self):
        for wizard in self:
            wizard.currency_id = wizard.payment_journal_id.currency_id or wizard.company_id.currency_id

    @api.depends('company_id')
    def _compute_payment_journal_id(self):
        for wizard in self:
            domain = [
                ('type', 'in', ('bank', 'cash')),
                ('company_id', '=', wizard.company_id.id),
            ]
            journal = self.env['account.journal'].search(domain, limit=1)
            wizard.payment_journal_id = journal

    def create_bank_slip_entry(self):
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(self._context.get('active_ids'))
        balance = self.currency_id._convert(abs(self.amount_in_bank_slip), self.company_currency_id, self.company_id, self.payment_date)
        debit_vals = {
            'name': 'Bank Slip',
            'account_id': self.payment_journal_id.default_account_id.id,
            'journal_id': self.payment_journal_id.id,
            'currency_id' : self.currency_id.id,
            'date': self.payment_date,
            'amount_currency': abs(self.amount_in_bank_slip),
            'debit': balance > 0.0 and balance or 0.0,
            'credit': 0.0,

        }
        credit_vals = {
            'name': 'Bank Slip',
            'account_id': records.journal_id.default_account_id.id,
            'journal_id': self.payment_journal_id.id,
            'currency_id' : self.currency_id.id,
            'date': self.payment_date,
            'amount_currency': - abs(self.amount_in_bank_slip),
            'debit': 0.0,
            'credit': balance > 0.0 and balance or 0.0,
        }
        vals = {
            'shipment_id': records.shipment_id.id,
            'ref': 'Bank Slip',
            'journal_id': self.payment_journal_id.id,
            'currency_id' : self.currency_id.id,
            'date': self.payment_date,
            'line_ids': [(0, 0, debit_vals), (0, 0, credit_vals)]
        }
        move = self.env['account.move'].create(vals)
        move.post()
        return True