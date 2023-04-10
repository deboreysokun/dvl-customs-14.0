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

from datetime import date, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from collections import defaultdict
from odoo.tools import date_utils
import re
import datetime
import json
from json import dumps


class OtherOperation(models.Model):
    _name = "other.operation"
    _order = "name desc"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'sequence.mixin']
    _description = "Other Service Operation"
    _check_company_auto = True
    _sequence_index = "service_type_id"

    @property
    def _sequence_monthly_regex(self):
        return self.service_type_id.sequence_override_regex or super()._sequence_monthly_regex

    @property
    def _sequence_yearly_regex(self):
        return self.service_type_id.sequence_override_regex or super()._sequence_yearly_regex

    @property
    def _sequence_fixed_regex(self):
        return self.service_type_id.sequence_override_regex or super()._sequence_fixed_regex

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """
            Override read_group to calculate the sum of the non-stored fields that depend on the user context
        """
        res = super(OtherOperation, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        operations = self.env['other.operation']
        for operation in res:
            if '__domain' in operation:
                operations = self.search(operation['__domain'])
            if 'total_invoices_amount' in fields:
                operation['total_invoices_amount'] = sum(operations.mapped('total_invoices_amount'))
            if 'total_expense_amount' in fields:
                operation['total_expense_amount'] = sum(operations.mapped('total_expense_amount'))
            if 'balance' in fields:
                operation['balance'] = sum(operations.mapped('balance'))
            if 'total_cash_received' in fields:
                operation['total_cash_received'] = sum(operations.mapped('total_cash_received'))
            if 'total_cash_paid' in fields:
                operation['total_cash_paid'] = sum(operations.mapped('total_cash_paid'))
            if 'cash_balance' in fields:
                operation['cash_balance'] = sum(operations.mapped('cash_balance'))
        return res

    company_id = fields.Many2one(comodel_name='res.company', string='Company',
        default=lambda self: self.env.company)
    active = fields.Boolean('Active', default=True, tracking=True)

    name = fields.Char(string='N0.',copy=False, compute='_compute_name', readonly=False, store=True, index=True, tracking=True)
    date = fields.Date(string='Date', required=True, index=True, readonly=True,
        states={'draft': [('readonly', False)]}, copy=False, default=fields.Date.context_today)
    service_type_id = fields.Many2one('other.operation.type', string="Operation Type")
    description = fields.Char(tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer", tracking=True)
    customer_feedback = fields.Text(tracking=True)

    start_date = fields.Date(default=fields.Date.context_today,tracking=True)
    end_date = fields.Date(tracking=True)
    note = fields.Text('Internal Note', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Open'),
        ('done', 'Finished')], string='Status', default='draft',
        store=True, tracking=True, copy=False, readonly=True)

    ######################### For Operation Money Transfer ###############################
    transfer_country_id = fields.Many2one('res.country', string="Country Transfer")
    received_country_id = fields.Many2one('res.country', string="Country Received")
    ######################### END For Operation Money Transfer  ###########################

    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')

    company_currency_id = fields.Many2one('res.currency', string="Company Currency", related='company_id.currency_id')
    is_editable = fields.Boolean(default=True ,help="Technical field to restrict editing.", copy=False)
    other_operation_expense_line_ids = fields.One2many('other.operation.expense.line', 'other_operation_id', copy=False)

    sale_quotation_id = fields.Many2one('sale.quotation', tracking=True, copy=False)

    ###################### Accounting Relating Fields #######################

    is_partially_paid = fields.Boolean(string="Partially Paid",readonly=1,copy=False, compute="_compute_invoice_state", compute_sudo=True)
    is_fully_paid = fields.Boolean(string="Fully Paid",readonly=1,copy=False, compute="_compute_invoice_state", compute_sudo=True)

    invoice_ids = fields.One2many(string='Related Invoices',  inverse_name='other_service_id',comodel_name='account.move',
        domain=[('state', '=', 'posted'),('move_type', 'in', ('out_invoice', 'out_refund')), ('journal_id.is_reimbursement', '=', False)])

    total_invoices_amount = fields.Monetary(currency_field='company_currency_id',compute='_total_invoices_amount', string="Total Revenue",
        groups='account.group_account_invoice')
    total_expense_amount = fields.Monetary(currency_field='company_currency_id',compute='_compute_total_expense_amount',
        groups='account.group_account_invoice,account.group_account_readonly', string="Total Expense")
    balance = fields.Monetary(currency_field='company_currency_id',compute='_balance',
        groups='account.group_account_invoice,account.group_account_readonly')

    ######################### Cash Paid and Cash Received  ###########################

    total_cash_received = fields.Monetary(currency_field='company_currency_id',compute='_compute_total_cash_received', string="Total Cash Received",
        groups='account.group_account_invoice,account.group_account_readonly')
    total_cash_paid = fields.Monetary(currency_field='company_currency_id',compute='_compute_total_cash_paid', string="Total Cash Paid",
        groups='account.group_account_invoice,account.group_account_readonly')
    cash_balance = fields.Monetary(currency_field='company_currency_id',compute='_balance',
        groups='account.group_account_invoice,account.group_account_readonly')

    ############################################################################################################
    # This number computed based on operation service type short code (following invoice sequence number concept)
    # borrow from  create Journal concept
    @api.depends('state', 'service_type_id','date')
    def _compute_name(self):
        def service_type_key(record):
            return (record.service_type_id)

        def date_key(record):
            return (record.date.year, record.date.month)

        grouped = defaultdict(  # key: service_type_id,
            lambda: defaultdict(  # key: first adjacent (date.year, date.month)
                lambda: {
                    'records': self.env['other.operation'],
                    'format': False,
                    'format_values': False,
                    'reset': False
                }
            )
        )
        self = self.sorted(lambda r: (r.date, r.id))
        highest_name = self[0]._get_last_sequence() if self else False

        # Group the moves by sevice type and month
        for record in self:
            if not highest_name and record == self[0] and record.date:
                # In the form view, we need to compute a default sequence so that the user can edit
                # it. We only check the first move as an approximation (enough for new in form view)
                pass
            elif (record.name and record.name != '/') or record.state != 'confirm':
                try:
                    continue
                except ValidationError:
                    # Has never been posted and the name doesn't match the date: recompute it
                    pass
            group = grouped[service_type_key(record)][date_key(record)]
            if not group['records']:
                # Compute all the values needed to sequence this whole group
                record._set_next_sequence()
                group['format'], group['format_values'] = record._get_sequence_format_param(record.name)
                group['reset'] = record._deduce_sequence_number_reset(record.name)
            group['records'] += record

        # Fusion the groups depending on the sequence reset and the format used because `seq` is
        # the same counter for multiple groups that might be spread in multiple months.
        final_batches = []
        for service_type_group in grouped.values():
            service_type_group_changed = True
            for date_group in service_type_group.values():
                if (
                    service_type_group_changed
                    or final_batches[-1]['format'] != date_group['format']
                    or dict(final_batches[-1]['format_values'], seq=0) != dict(date_group['format_values'], seq=0)
                ):
                    final_batches += [date_group]
                    service_type_group_changed = False
                elif date_group['reset'] == 'never':
                    final_batches[-1]['records'] += date_group['records']
                elif (
                    date_group['reset'] == 'year'
                    and final_batches[-1]['records'][0].date.year == date_group['records'][0].date.year
                ):
                    final_batches[-1]['records'] += date_group['records']
                else:
                    final_batches += [date_group]

        # Give the name based on previously computed values
        for batch in final_batches:
            for service in batch['records']:
                service.name = batch['format'].format(**batch['format_values'])
                batch['format_values']['seq'] += 1
            batch['records']._compute_split_sequence()

        self.filtered(lambda r: not r.name).name = '/'

    def _get_last_sequence_domain(self, relaxed=False):
        self.ensure_one()
        if not self.date or not self.service_type_id:
            return "WHERE FALSE", {}
        where_string = "WHERE service_type_id = %(service_type_id)s AND name != '/'"
        param = {'service_type_id': self.service_type_id.id}

        if not relaxed:
            domain = [('service_type_id', '=', self.service_type_id.id), ('id', '!=', self.id or self._origin.id), ('name', 'not in', ('/', False))]

            reference_record_name = self.search(domain + [('date', '<=', self.date)], order='date desc', limit=1).name
            if not reference_record_name:
                reference_record_name = self.search(domain, order='date asc', limit=1).name
            sequence_number_reset = self._deduce_sequence_number_reset(reference_record_name)
            if sequence_number_reset == 'year':
                where_string += " AND date_trunc('year', date::timestamp without time zone) = date_trunc('year', %(date)s) "
                param['date'] = self.date
                param['anti_regex'] = re.sub(r"\?P<\w+>", "?:", self._sequence_monthly_regex.split('(?P<seq>')[0]) + '$'
            elif sequence_number_reset == 'month':
                where_string += " AND date_trunc('month', date::timestamp without time zone) = date_trunc('month', %(date)s) "
                param['date'] = self.date
            else:
                param['anti_regex'] = re.sub(r"\?P<\w+>", "?:", self._sequence_yearly_regex.split('(?P<seq>')[0]) + '$'

            if param.get('anti_regex') and not self.service_type_id.sequence_override_regex:
                where_string += " AND sequence_prefix !~ %(anti_regex)s "

        return where_string, param

    def _get_starting_sequence(self):
        self.ensure_one()
        starting_sequence = "%s/%04d/%02d/000" % (self.service_type_id.code, self.date.year, self.date.month)
        return starting_sequence
    ############################################################################################################

    @api.depends('invoice_ids.payment_state')
    def _compute_invoice_state(self):
        for record in self:
            record.is_fully_paid = record.is_partially_paid = False
            domain = [
                ('other_service_id', '=', record.id),
                ('state', 'not in', ['cancel', 'draft']),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('journal_id.is_reimbursement', '=', False), # excluded reimbursement journal
            ]
            invoices = self.env['account.move'].search(domain)
            for invoice in invoices:
                if (invoice.payment_state == "paid" or invoice.payment_state == "partial"):
                    if invoice.payment_state == 'partial':
                        record.write({
                        "is_partially_paid": True,
                        "is_fully_paid": False,
                    })
                    amount = 0
                    if invoice.payment_state == 'paid' and invoice.amount_residual_signed == 0:
                        if invoice.move_type in ('out_refund'):
                            amount -= invoice.amount_total_signed
                        else:
                            amount += invoice.amount_total_signed
                    if amount == invoice.amount_total_signed:
                        record.write({
                            "is_partially_paid": False,
                            "is_fully_paid": True
                        })
                else:
                    record.write({
                        "is_fully_paid": False
                    })

    def _total_invoices_amount(self):
        for record in self:
            record.total_invoices_amount = 0
            if not self.ids:
                return True
            domain = [
                ('other_service_id', '=', record.id),
                ('state', 'not in', ['cancel']),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('journal_id.is_reimbursement', '=', False), # excluded reimbursement journal
            ]
            price_totals = self.env['account.move'].read_group(domain, ['amount_total_signed'], ['other_service_id'])
            record.total_invoices_amount = sum(amount['amount_total_signed'] for amount in price_totals)

    def action_view_invoice(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [
            ('other_service_id', '=', self.id),
            ('state', 'not in', ['cancel']),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('journal_id.is_reimbursement', '=', False), # excluded reimbursement journal
        ]
        journal_id = self.env['account.journal'].search([('name', '=ilike', self.service_type_id.name)], limit=1)
        action['context'] = {
            'default_move_type': 'out_invoice',
            'default_other_service_id': self.id,
            'default_invoice_origin': self.name,
            'default_journal_id': journal_id.id,
        }
        return action

    @api.depends('other_operation_expense_line_ids.sub_total')
    def _compute_total_expense_amount(self):
        for record in self:
            line = record.other_operation_expense_line_ids.filtered(lambda l: l.state != 'reject')
            record.total_expense_amount = - sum(line.mapped('sub_total'))

    @api.onchange('total_invoices_amount', 'total_expense_amount', 'total_cash_received', 'total_cash_paid')
    def _balance(self):
        for record in self:
            record.balance = record.total_invoices_amount - abs(record.total_expense_amount)
            record.cash_balance = record.total_cash_received - abs(record.total_cash_paid)

    def _compute_total_cash_received(self):
        for record in self:
            record.total_cash_received = cash_received = 0
            if not self.ids:
                return True
            domain_invoice=[
                ('state', '=', 'posted'),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('other_service_id', '=', record.id)
            ]
            invoices = self.env['account.move'].search(domain_invoice)
            for invoice in invoices:
                cash_received += invoice.amount_total_signed - invoice.amount_residual_signed

            domain = [
                ('move_id.other_service_id', '=', record.id),
                ('move_id.state', 'not in', ['draft', 'cancel']),
                ('move_id.move_type', 'not in', ['in_invoice', 'in_refund', 'in_receipt']),
                ('account_id.user_type_id', '=', self.env.ref('account.data_account_type_liquidity').id), # I want to get only bank and cash account
            ]
            debit = self.env['account.move.line'].read_group(domain, ['debit'], ['move_id']) # since it's cash received; get debit side only
            cash_received += sum(amount['debit'] for amount in debit)
            record.total_cash_received = cash_received

    def _get_revenue_invoice_ids(self):
        invoice_payment_info = {}
        invoice_payment_ids = []
        payment_account_move_ids = []
        for invoice_id in self.invoice_ids:
            invoice_payment_info = invoice_id._get_reconciled_info_JSON_values()
            for payment_vals in invoice_payment_info:
                payment_id = self.env['account.payment'].browse(payment_vals['account_payment_id'])
                invoice_payment_ids.append(payment_id)

        for payment_id in invoice_payment_ids:
            payment_account_move_ids.append(payment_id.move_id.id)

        return payment_account_move_ids

    def action_view_cash_received_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_moves_all")
        account_move_ids = self._get_revenue_invoice_ids() or []
        action['domain'] = ["|", ('move_id', 'in', account_move_ids),
            ('move_id.other_service_id', '=', self.id),
            '&', ('move_id.state', '=', 'posted'),
            ('move_id.move_type', 'in', ['entry']),
            ('account_id.user_type_id', '=', self.env.ref('account.data_account_type_liquidity').id),
        ]
        return action

    @api.depends('total_expense_amount')
    def _compute_total_cash_paid(self):
        for record in self:
            record.total_cash_paid = cash_paid =0
            if not self.ids:
                return True
            domain = [
                ('move_id.other_service_id', '=', record.id),
                ('move_id.state', 'not in', ['draft', 'cancel']),
                ('move_id.move_type', 'not in', ['in_invoice', 'in_refund', 'in_receipt']),
                ('account_id.user_type_id', '=', self.env.ref('account.data_account_type_liquidity').id), # I want to get only bank and cash account
            ]
            credit = self.env['account.move.line'].read_group(domain, ['credit'], ['move_id'])
            cash_paid += sum(amount['credit'] for amount in credit) #since it's cash paid; get credit side only
            record.total_cash_paid = - cash_paid

    def action_view_cash_paid_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_account_moves_all")
        action['domain'] = [
            ('move_id.other_service_id', '=', self.id),
            ('move_id.state', 'not in', ['draft', 'cancel']),
            ('move_id.move_type', 'not in', ['in_refund', 'out_invoice', 'out_receipt']),
            ('account_id.user_type_id', 'in', [15, 17]),#type 15-Expense, 17-Cost of Revenue)
        ]
        return action

    def action_confirm(self):
        for record in self:
            record.write({'state': 'confirm', 'is_editable': True})
        return True

    def action_done(self):
        for record in self:
            record.write({'state': 'done', 'is_editable': False})
        return True

    def action_draft(self):
        for record in self:
            record.write({'state': 'draft', 'is_editable': True})
        return True

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'other.operation'), ('accounting_document', '=', False), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for record in self:
            record.attachment_number = attachment.get(record.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'other.operation'), ('res_id', 'in', self.ids), ('accounting_document', '=', False)]
        res['context'] = {'default_res_model': 'other.operation', 'default_res_id': self.id}
        return res

    def action_get_attachment_accounting_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'other.operation'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'other.operation', 'default_res_id': self.id, 'default_accounting_document': True}
        return res

    def action_open(self):
        self.ensure_one()
        # I want to open the view in a new tab, if you can find a better way, please fix me!
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        if self._context.get('other_opperation_report'):
            menu_id = self.env.ref('devel_logistic_management.dvl_main_menu').id
            action_id = self.env.ref("devel_other_operation.dvl_report_other_operation_action").id
        else:
            menu_id = self.env.ref('devel_other_operation.dvl_other_service_type_menu').id
            action_id = self.env.ref("devel_other_operation.action_view_other_operation_tree").id
        return {
            'type': 'ir.actions.act_url',
            'target': '_blank',
            'url': str(base_url) + "/web#id=%s&action=%s&model=operation.shipment&view_type=form&cids=%s&menu_id=%s" % (self.id, action_id, self.env.company.id, menu_id),
        }

    def unlink(self):
        if any(record.state in ('confirm', 'done') for record in self):
            raise UserError(_('You cannot delete a record that is Open or Finish.'))
        if any((record.total_invoices_amount != 0 or record.total_expense_amount != 0) for record in self):
            raise UserError(_('You cannot delete a record that already has Revenues or Expenses!'))
        return super(OtherOperation, self).unlink()

class OtherOperationType(models.Model):
    _name = "other.operation.type"
    _order = "sequence, code, name desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Other Service Type"


    name = fields.Char()
    code = fields.Char(string='Short Code', size=6, required=True, help="Shorter name used for display. The record will also be named using this prefix by default.")
    color = fields.Integer("Color Index", default=0)
    sequence = fields.Integer(help='Used to order Service type in the dashboard view', default=10)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)

    check_sequence_id = fields.Many2one(comodel_name='ir.sequence',string='Check Sequence',
        readonly=True,copy=False,help="Checks numbering sequence.",)
    sequence_override_regex = fields.Text(help="Technical field used to enforce complex sequence composition that the system would normally misunderstand.\n"\
                                            "This is a regex that can include all the following capture groups: prefix1, year, prefix2, month, prefix3, seq, suffix.\n"\
                                            "The prefix* groups are the separators between the year, month and the actual increasing sequence number (seq).\n"\

                                            "e.g: ^(?P<prefix1>.*?)(?P<year>\d{4})(?P<prefix2>\D*?)(?P<month>\d{2})(?P<prefix3>\D+?)(?P<seq>\d+)(?P<suffix>\D*?)$")

    _sql_constraints = [
        ('code_company_uniq', 'unique (code, name, company_id)', 'The code and name of the service type must be unique per company !'),
    ]

    @api.model
    def create(self, vals):
        rec = super(OtherOperationType, self).create(vals)
        if not rec.check_sequence_id:
            rec._create_check_sequence()
        return rec

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        rec = super(OtherOperationType, self).copy(default)
        rec._create_check_sequence()
        return rec

    def _create_check_sequence(self):
        """ Create a check sequence for the operation service type """
        for service_type in self:
            service_type.check_sequence_id = self.env['ir.sequence'].sudo().create({
                'name': service_type.name + _(" : Check Number Sequence"),
                'implementation': 'no_gap',
                'padding': 3,
                'number_increment': 1,
                'company_id': service_type.company_id.id,
            })

    def action_create_new(self):
        ctx = self._context.copy()
        ctx['default_service_type_id'] = self.id
        return {
            'name': _('Create Other Service'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'other.operation',
            'view_id': self.env.ref('devel_other_operation.view_other_operation_form').id,
            'context': ctx,
        }

    def open_action(self):
        """return action based on type for related journals"""
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id('devel_other_operation.action_view_other_operation_tree')

        action['domain'] = [('service_type_id', '=', self.id)]
        action['context'] = {
            'default_service_type_id': self.id,
            'search_default_service_type_id': self.id,
        }
        return action

class OtherOperationExpenseLine(models.Model):
    _name = "other.operation.expense.line"
    _order = "sequence, id desc"
    _description = "Other Service Expense Line"
    _check_company_auto = True

    @api.returns('self')
    def _get_default_currency(self):
        return self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True,
        states={'draft': [('readonly', False)]},
        string='Currency',
        default=_get_default_currency)
    rate = fields.Float(string='Currency Rate', store=True, readonly=True, compute="_compute_subtotal_amount", copy=False)
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of lines.",default=10)

    other_operation_id = fields.Many2one('other.operation', ondelete='cascade')
    description = fields.Char()
    qty = fields.Float(default=1.0, tracking=True, string="QTY")
    uom_id = fields.Many2one('uom.unit', string="UOM", default=lambda self: self.env['uom.unit'].search([('id', '=', 77)]))
    unit_price = fields.Float(tracking=True, copy=False)
    sub_total = fields.Float(store=True, compute="_compute_subtotal_amount",tracking=True, copy=False)
    company_id = fields.Many2one(related='other_operation_id.company_id', store=True, readonly=True, default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="cascade", check_company=True, tracking=True,
        domain="[('deprecated', '=', False),('user_type_id.type', 'not in', ('receivable', 'payable')),('is_off_balance', '=', False),('user_type_id', '=', 17)]")
    state = fields.Selection([
        ('draft', 'To Confirm'),
        ('confirm', 'To Approve'),
        ('validate', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
        ('direct_paid', 'Direct Paid')], string='Status',
        default='draft', store=True, tracking=True, copy=False, readonly=False,)
    move_id = fields.Many2one('account.move', copy=False)

    requester_user_id = fields.Many2one('res.users', string='Requested By', compute_sudo=True, store=True, readonly=True,
        domain=[('active', '=', True)], copy=False)
    requested_date = fields.Datetime(tracking=True, copy=False, default=lambda self: fields.Datetime.now())
    checked_user_id = fields.Many2one('res.users', string='Checked By', compute_sudo=True, store=True,  readonly=True, copy=False,
        domain=[('active', '=', True)])
    checked_date = fields.Datetime(tracking=True, copy=False)
    approver_user_id = fields.Many2one('res.users', string='Approved By', compute_sudo=True, store=True, readonly=True, copy=False,
        domain=[('active', '=', True)])
    approved_date = fields.Datetime(tracking=True, copy=False)
    paid_user_id = fields.Many2one('res.users', string='Paid By', compute_sudo=True, store=True, readonly=True, copy=False,
        domain=[('active', '=', True)])
    paid_date = fields.Date(tracking=True, copy=False)
    received_user_id = fields.Many2one('res.partner', string='Received By', compute_sudo=True, store=True, copy=False,
        domain=[('active', '=', True)])
    receiver_bank_info_widget = fields.Text(compute='_compute_receiver_bank_info_widget')
    remark = fields.Text(string="Remark", readonly=False, copy=False)
    is_editable = fields.Boolean(related="other_operation_id.is_editable",store=True,help="Technical field to restrict editing.")

    @api.depends('received_user_id')
    def _get_account_bank_info_JSON_values(self):
        self.ensure_one()
        bank_lines_vals = []
        for bank_id in self.received_user_id.bank_ids:
            bank_lines_vals.append({
                'bank_name': bank_id.bank_id.name,
                'acc_name': bank_id.acc_holder_name,
                'acc_number': bank_id.acc_number,
            })
        return bank_lines_vals

    @api.depends('received_user_id')
    def _compute_receiver_bank_info_widget(self):
        for line in self:
            banks_widget_vals = {'title': _('Bank Info'), 'content': []}

            if line.received_user_id.bank_ids:
                banks_widget_vals['content'] = line._get_account_bank_info_JSON_values()

            if banks_widget_vals['content']:
                line.receiver_bank_info_widget = json.dumps(banks_widget_vals, default=date_utils.json_default)
            else:
                line.receiver_bank_info_widget = json.dumps(False)

    def _compute_request_date(self):
        for line in self:
            if line.requested_date == False:
                line.requested_date = line.create_date

    @api.depends('qty', 'unit_price', 'currency_id')
    def _compute_subtotal_amount(self):
        for line in self:
            line.sub_total = line.currency_id._convert(line.unit_price, line.company_id.currency_id, line.company_id, line.requested_date) * line.qty
            currency_rates = line.currency_id._get_rates(line.company_id, line.requested_date)
            line.rate = currency_rates.get(line.currency_id.id) or 1.0

    @api.onchange('currency_id')
    def _onchange_currency(self):
        for line in self:
            line.sub_total = line.currency_id._convert(line.unit_price, line.company_id.currency_id, line.company_id, line.requested_date) * line.qty
            currency_rates = line.currency_id._get_rates(line.company_id, line.requested_date)
            line.rate = currency_rates.get(line.currency_id.id) or 1.0

    def action_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_other_operation.group_dvl_other_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to confirm this!'))
        if self.filtered(lambda request: request.state != 'draft'):
            raise UserError(_('Request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm', 'checked_user_id': self.env.user.id, 'checked_date': datetime.datetime.today()})
        return True

    def action_approve(self):
        is_manager = self.env.user.has_group('devel_other_operation.group_dvl_other_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to approve it.'))
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'validate', 'approver_user_id': self.env.user.id, 'approved_date':datetime.datetime.today()})
        return True

    def action_confirm_approve(self):
        is_manager = self.env.user.has_group('devel_other_operation.group_dvl_other_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'draft' for request in self):
            raise UserError(_('Expense Line must be Draft in order to Approve it.'))
        self.filtered(lambda request: request.state == 'draft').write({
            'state': 'validate',
            'approver_user_id': self.env.user.id, 'approved_date':datetime.datetime.today(),
            'checked_user_id': self.env.user.id, 'checked_date':datetime.datetime.today(),
            })
        return True

    def action_reject(self):
        is_manager = self.env.user.has_group('devel_other_operation.group_dvl_other_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to reject this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to reject it.'))
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'reject'})
        return True

    def action_draft_user_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_other_operation.group_dvl_other_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink()
        })
        self._compute_subtotal_amount()
        return True

    def action_draft(self):
        is_manager = self.env.user.has_group('devel_other_operation.group_dvl_other_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'approver_user_id': False,
            'approved_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink()
        })
        self._compute_subtotal_amount()
        return True

    def _check_line_unlink(self):
        """
        Check wether a line can be deleted or not.

        Lines cannot be deleted if the status is Approved and Paid
        :returns: set of lines that cannot be deleted
        """
        return self.filtered(lambda line: line.state in ('validate', 'paid', 'direct_paid'))

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove a request that is already Approved or Paid.'))
        return super(OtherOperationExpenseLine, self).unlink()

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class OtherOperationExpenseLine(models.Model):
    _name = "all.expense.shipment"
    _order = "sequence, id desc"
    _description = "Other Service Expense Line"
    _check_company_auto = True

class OtherOperationExpenseLine(models.Model):
    _name = "shipment.expense.all.lines"
    _order = "sequence, id desc"
    _description = "Other Service Expense Line"
    _check_company_auto = True