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

import pytz
import datetime
from datetime import date
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import date_utils
from json import dumps

import json

class ShipmentExpenseOfficePermit(models.Model):
    _name = "shipment.expense.customs.office.permit"
    _order = 'shipment_id, sequence, id'
    _description = "Shipment Expense line for Customs Office and Permit"
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
    shipment_id = fields.Many2one('operation.shipment', ondelete='cascade')
    description = fields.Char(tracking=True)
    qty = fields.Float(default=1.0, tracking=True, string="QTY")
    uom_id = fields.Many2one('uom.unit', string="UOM", default=lambda self: self.env['uom.unit'].search([('id', '=', 77)]), tracking=True,)
    unit_price = fields.Float(tracking=True, copy=False)
    sub_total = fields.Float(store=True, compute="_compute_subtotal_amount",tracking=True, copy=False)
    company_id = fields.Many2one(related='shipment_id.company_id', store=True, readonly=True, default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="cascade",
        domain="[('deprecated', '=', False),('user_type_id.type', 'not in', ('receivable', 'payable')),('is_off_balance', '=', False),(('user_type_id', '=', 17))]",
        check_company=True,
        tracking=True)
    state = fields.Selection([
        ('draft', 'To Confirm'),
        ('confirm', 'To Approve'),
        ('validate', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
        ('direct_paid', 'Direct Paid'),
        ('reimbursed', 'Reimbursed'),
        ], string='Status', default='draft', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Confirm', when request is created." +
        "\nThe status is 'To Approve', when request is checked by user." +
        "\nThe status is 'Approved', when request is approved by user." +
        "\nThe status is 'Paid', when request is paid by user." +
        "\nThe status is 'Direct Paid', bypass Confirm, Validate, and Approve state by user." +
        "\nThe status is 'Reimbursed', when any expenses are not company actual expenses. Subtotal will be zero")
    move_id = fields.Many2one('account.move', copy=False)
    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')

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
    reason = fields.Text(string="Reason", readonly=True, copy=False)
    remark_expense = fields.Char(string="Remark", copy=False)
    clear_advance = fields.Boolean(default=False, string='Clear Advance?', copy=False, readonly=True)

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
            line.sub_total = line.currency_id._convert(line.unit_price, line.company_id.currency_id, line.company_id, line.requested_date or fields.Date.today()) * line.qty
            currency_rates = line.currency_id._get_rates(line.company_id, line.requested_date or fields.Date.today())
            line.rate = currency_rates.get(line.currency_id.id) or 1.0

    @api.onchange('currency_id')
    def _onchange_currency(self):
        for line in self:
            line.sub_total = line.currency_id._convert(line.unit_price, line.company_id.currency_id, line.company_id, line.requested_date) * line.qty
            currency_rates = line.currency_id._get_rates(line.company_id, line.requested_date)
            line.rate = currency_rates.get(line.currency_id.id) or 1.0

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'shipment.expense.customs.office.permit'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'shipment.expense.customs.office.permit'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'shipment.expense.customs.office.permit', 'default_res_id': self.id}
        return res

    def action_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to confirm this!'))
        if self.filtered(lambda request: request.state != 'draft'):
            raise UserError(_('Request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm', 'checked_user_id': self.env.user.id, 'checked_date': datetime.datetime.today()})
        return True

    def action_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'validate', 'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today()})
        return True

    def action_confirm_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'draft' for request in self):
            raise UserError(_('Expense Line must be Draft in order to Approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'draft').write({
            'state': 'validate',
            'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today(),
            'checked_user_id': current_user.id, 'checked_date':datetime.datetime.today(),
            })
        return True

    def action_reject(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to reject this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to reject it.'))
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'reject'})
        return True

    def action_draft_user_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def action_draft(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'approver_user_id': False,
            'approved_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def _check_line_unlink(self):
        """
        Check wether a line can be deleted or not.

        Lines cannot be deleted if the status is Approved and Paid or Reimbursed
        :returns: set of lines that cannot be deleted
        """
        return self.filtered(lambda line: line.state in ('validate', 'paid', 'direct_paid', 'reimbursed'))

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove a request that is already Approved or Paid or Reimbursed.'))
        return super(ShipmentExpenseOfficePermit, self).unlink()

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class ShipmentExpenseShippingLine(models.Model):
    _name = "shipment.expense.shipping.line"
    _order = 'shipment_id, sequence, id'
    _description = "Shipment Expense line for Shipping Line"
    _check_company_auto = True

    @api.returns('self')
    def _get_default_currency(self):
        return self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True,
        states={'draft': [('readonly', False)]},
        string='Currency',
        default=_get_default_currency)
    rate = fields.Float(string='Currency Rate', store=True, readonly=True, compute="_compute_subtotal_amount")

    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of lines.",default=10)
    shipment_id = fields.Many2one('operation.shipment', ondelete='cascade')
    description = fields.Char(tracking=True)
    qty = fields.Float(default=1.0, tracking=True, string="QTY")
    uom_id = fields.Many2one('uom.unit', string="UOM", default=lambda self: self.env['uom.unit'].search([('id', '=', 77)]))
    unit_price = fields.Float(tracking=True, copy=False)
    sub_total = fields.Float(store=True, compute="_compute_subtotal_amount", tracking=True, copy=False)
    company_id = fields.Many2one(related='shipment_id.company_id', store=True, readonly=True, default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="cascade",
        domain="[('deprecated', '=', False),('is_off_balance', '=', False),(('user_type_id', 'in', (17, 19)))]", #19=Other Receivable for Container deposit
        check_company=True,
        tracking=True)
    state = fields.Selection([
        ('draft', 'To Confirm'),
        ('confirm', 'To Approve'),
        ('validate', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
        ('direct_paid', 'Direct Paid'),
        ('reimbursed', 'Reimbursed'),
        ], string='Status', default='draft', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Confirm', when request is created." +
        "\nThe status is 'To Approve', when request is checked by user." +
        "\nThe status is 'Approved', when request is approved by user." +
        "\nThe status is 'Paid', when request is paid by user." +
        "\nThe status is 'Direct Paid', bypass Confirm, Validate, and Approve state by user." +
        "\nThe status is 'Reimbursed', when any expenses are not company actual expenses. Subtotal will be zero")
    move_id = fields.Many2one('account.move', copy=False)

    thc_amount = fields.Boolean('THC Amount?', help='Green this button when this amount is calulate as THC AMOUNT.', copy=True)

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
    reason = fields.Text(string="Reason", readonly=True, copy=False)
    remark_expense = fields.Char(string="Remark", copy=False)
    clear_advance = fields.Boolean(default=False, string='Clear Advance?', copy=False, readonly=True)

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

    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'shipment.expense.shipping.line'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'shipment.expense.shipping.line'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'shipment.expense.shipping.line', 'default_res_id': self.id}
        return res

    def _compute_request_date(self):
        for line in self:
            if line.requested_date == False:
                line.requested_date = line.create_date

    @api.depends('qty', 'unit_price', 'currency_id')
    def _compute_subtotal_amount(self):
        for line in self:
            line.sub_total = line.currency_id._convert(line.unit_price, line.company_id.currency_id, line.company_id, line.requested_date or fields.Date.today()) * line.qty
            currency_rates = line.currency_id._get_rates(line.company_id, line.requested_date or fields.Date.today())
            line.rate = currency_rates.get(line.currency_id.id) or 1.0

    @api.onchange('currency_id')
    def _onchange_currency(self):
        for line in self:
            line.sub_total = line.currency_id._convert(line.unit_price, line.company_id.currency_id, line.company_id, line.requested_date) * line.qty
            currency_rates = line.currency_id._get_rates(line.company_id, line.requested_date)
            line.rate = currency_rates.get(line.currency_id.id) or 1.0

    def action_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to confirm this!'))
        if self.filtered(lambda request: request.state != 'draft'):
            raise UserError(_('Request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm', 'checked_user_id': self.env.user.id, 'checked_date': datetime.datetime.today()})
        return True

    def action_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'validate', 'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today()})
        return True

    def action_confirm_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'draft' for request in self):
            raise UserError(_('Expense Line must be Draft in order to Approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'draft').write({
            'state': 'validate',
            'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today(),
            'checked_user_id': current_user.id, 'checked_date':datetime.datetime.today(),
            })
        return True

    def action_reject(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to reject this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to reject it.'))
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'reject'})
        return True

    def action_draft_user_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def action_draft(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'approver_user_id': False,
            'approved_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def _check_line_unlink(self):
        """
        Check wether a line can be deleted or not.

        Lines cannot be deleted if the status is Approved and Paid or Reimbursed
        :returns: set of lines that cannot be deleted
        """
        return self.filtered(lambda line: line.state in ('validate', 'paid', 'direct_paid', 'reimbursed'))

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove a request that is already Approved or Paid or Reimbursed.'))
        return super(ShipmentExpenseShippingLine, self).unlink()

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class ShipmentExpenseClearance(models.Model):
    _name = "shipment.expense.clearance"
    _order = 'shipment_id, sequence, id'
    _description = "Shipment Expense line for Clearance"
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
    shipment_id = fields.Many2one('operation.shipment', ondelete='cascade')
    description = fields.Char()
    qty = fields.Float(default=1.0, tracking=True, string="QTY")
    uom_id = fields.Many2one('uom.unit', string="UOM", default=lambda self: self.env['uom.unit'].search([('id', '=', 77)]))
    unit_price = fields.Float(tracking=True, copy=False)
    sub_total = fields.Float(store=True, compute="_compute_subtotal_amount", tracking=True, copy=False)
    company_id = fields.Many2one(related='shipment_id.company_id', store=True, readonly=True, default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="cascade",
        domain="[('deprecated', '=', False),('user_type_id.type', 'not in', ('receivable', 'payable')),('is_off_balance', '=', False),(('user_type_id', '=', 17))]",
        check_company=True,
        tracking=True)
    state = fields.Selection([
        ('draft', 'To Confirm'),
        ('confirm', 'To Approve'),
        ('validate', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
        ('direct_paid', 'Direct Paid'),
        ('reimbursed', 'Reimbursed'),
        ], string='Status', default='draft', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Confirm', when request is created." +
        "\nThe status is 'To Approve', when request is checked by user." +
        "\nThe status is 'Approved', when request is approved by user." +
        "\nThe status is 'Paid', when request is paid by user." +
        "\nThe status is 'Direct Paid', bypass Confirm, Validate, and Approve state by user." +
        "\nThe status is 'Reimbursed', when any expenses are not company actual expenses. Subtotal will be zero")
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
    reason = fields.Text(string="Reason", readonly=True, copy=False)
    remark_expense = fields.Char(string="Remark", copy=False)
    clear_advance = fields.Boolean(default=False, string='Clear Advance?', copy=False, readonly=True)

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

    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'shipment.expense.clearance'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'shipment.expense.clearance'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'shipment.expense.clearance', 'default_res_id': self.id}
        return res

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
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to confirm this!'))
        if self.filtered(lambda request: request.state != 'draft'):
            raise UserError(_('Request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm', 'checked_user_id': self.env.user.id, 'checked_date': datetime.datetime.today()})
        return True

    def action_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'validate', 'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today()})
        return True

    def action_confirm_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'draft' for request in self):
            raise UserError(_('Expense Line must be Draft in order to Approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'draft').write({
            'state': 'validate',
            'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today(),
            'checked_user_id': current_user.id, 'checked_date':datetime.datetime.today(),
            })
        return True

    def action_reject(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to reject this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to reject it.'))
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'reject'})
        return True

    def action_draft_user_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def action_draft(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'approver_user_id': False,
            'approved_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def _check_line_unlink(self):
        """
        Check wether a line can be deleted or not.

        Lines cannot be deleted if the status is Approved and Paid or Reimbursed
        :returns: set of lines that cannot be deleted
        """
        return self.filtered(lambda line: line.state in ('validate', 'paid', 'direct_paid', 'reimbursed'))

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove a request that is already Approved or Paid or Reimbursed.'))
        return super(ShipmentExpenseClearance, self).unlink()

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class ShipmentExpenseCustomDuty(models.Model):
    _name = "shipment.expense.custom.duty"
    _order = 'shipment_id, sequence, id'
    _description = "Shipment Expense line for Customs Duty"
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
    shipment_id = fields.Many2one('operation.shipment', ondelete='cascade')
    description = fields.Char()
    qty = fields.Float(default=1.0, tracking=True, string="QTY")
    uom_id = fields.Many2one('uom.unit', string="UOM", default=lambda self: self.env['uom.unit'].search([('id', '=', 77)]))
    unit_price = fields.Float(tracking=True, copy=False)
    sub_total = fields.Float(store=True, compute="_compute_subtotal_amount",tracking=True, copy=False)
    company_id = fields.Many2one(related='shipment_id.company_id', store=True, readonly=True, default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="cascade",
        domain="[('deprecated', '=', False),('user_type_id.type', 'not in', ('receivable', 'payable')),('is_off_balance', '=', False),(('user_type_id', '=', 17))]",
        check_company=True,
        tracking=True)
    state = fields.Selection([
        ('draft', 'To Confirm'),
        ('confirm', 'To Approve'),
        ('validate', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
        ('direct_paid', 'Direct Paid'),
        ('reimbursed', 'Reimbursed'),
        ], string='Status', default='draft', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Confirm', when request is created." +
        "\nThe status is 'To Approve', when request is checked by user." +
        "\nThe status is 'Approved', when request is approved by user." +
        "\nThe status is 'Paid', when request is paid by user." +
        "\nThe status is 'Direct Paid', bypass Confirm, Validate, and Approve state by user." +
        "\nThe status is 'Reimbursed', when any expenses are not company actual expenses. Subtotal will be zero")
    move_id = fields.Many2one('account.move', copy=False)
    duty_tax = fields.Boolean('Duty Tax?', help='Green this button when this amount is calulate as Duty Tax Amount.', copy=True)

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
    reason = fields.Text(string="Reason", readonly=True, copy=False)
    remark_expense = fields.Char(string="Remark", copy=False)
    clear_advance = fields.Boolean(default=False, string='Clear Advance?', copy=False, readonly=True)

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

    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'shipment.expense.custom.duty'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'shipment.expense.custom.duty'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'shipment.expense.custom.duty', 'default_res_id': self.id}
        return res

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
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to confirm this!'))
        if self.filtered(lambda request: request.state != 'draft'):
            raise UserError(_('Request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm', 'checked_user_id': self.env.user.id, 'checked_date': datetime.datetime.today()})
        return True

    def action_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'validate', 'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today()})
        return True

    def action_confirm_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'draft' for request in self):
            raise UserError(_('Expense Line must be Draft in order to Approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'draft').write({
            'state': 'validate',
            'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today(),
            'checked_user_id': current_user.id, 'checked_date':datetime.datetime.today(),
            })
        return True

    def action_reject(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to reject this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to reject it.'))
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'reject'})
        return True

    def action_draft_user_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def action_draft(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'approver_user_id': False,
            'approved_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def _check_line_unlink(self):
        """
        Check wether a line can be deleted or not.

        Lines cannot be deleted if the status is Approved and Paid or Reimbursed
        :returns: set of lines that cannot be deleted
        """
        return self.filtered(lambda line: line.state in ('validate', 'paid', 'direct_paid', 'reimbursed'))

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove a request that is already Approved or Paid or Reimbursed.'))
        return super(ShipmentExpenseCustomDuty, self).unlink()

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class ShipmentExpensePortCharge(models.Model):
    _name = "shipment.expense.port.charge"
    _order = 'shipment_id, sequence, id'
    _description = "Shipment Expense line for Port Charge"
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
    shipment_id = fields.Many2one('operation.shipment', ondelete='cascade')
    description = fields.Char()
    qty = fields.Float(default=1.0, tracking=True, string="QTY")
    uom_id = fields.Many2one('uom.unit', string="UOM", default=lambda self: self.env['uom.unit'].search([('id', '=', 77)]))
    unit_price = fields.Float(tracking=True, copy=False)
    sub_total = fields.Float(store=True, compute="_compute_subtotal_amount", tracking=True, copy=False)
    company_id = fields.Many2one(related='shipment_id.company_id', store=True, readonly=True, default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="cascade",
        domain="[('deprecated', '=', False),('user_type_id.type', 'not in', ('receivable', 'payable')),('is_off_balance', '=', False),(('user_type_id', '=', 17))]",
        check_company=True,
        tracking=True)
    state = fields.Selection([
        ('draft', 'To Confirm'),
        ('confirm', 'To Approve'),
        ('validate', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
        ('direct_paid', 'Direct Paid'),
        ('reimbursed', 'Reimbursed'),
        ], string='Status', default='draft', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Confirm', when request is created." +
        "\nThe status is 'To Approve', when request is checked by user." +
        "\nThe status is 'Approved', when request is approved by user." +
        "\nThe status is 'Paid', when request is paid by user." +
        "\nThe status is 'Direct Paid', bypass Confirm, Validate, and Approve state by user." +
        "\nThe status is 'Reimbursed', when any expenses are not company actual expenses. Subtotal will be zero")
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
    reason = fields.Text(string="Reason", readonly=True, copy=False)
    remark_expense = fields.Char(string="Remark", copy=False)
    clear_advance = fields.Boolean(default=False, string='Clear Advance?', copy=False, readonly=True)

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

    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'shipment.expense.port.charge'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'shipment.expense.port.charge'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'shipment.expense.port.charge', 'default_res_id': self.id}
        return res

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
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to confirm this!'))
        if self.filtered(lambda request: request.state != 'draft'):
            raise UserError(_('Request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm', 'checked_user_id': self.env.user.id, 'checked_date': datetime.datetime.today()})
        return True

    def action_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'validate', 'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today()})
        return True

    def action_confirm_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'draft' for request in self):
            raise UserError(_('Expense Line must be Draft in order to Approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'draft').write({
            'state': 'validate',
            'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today(),
            'checked_user_id': current_user.id, 'checked_date':datetime.datetime.today(),
            })
        return True

    def action_reject(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to reject this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to reject it.'))
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'reject'})
        return True

    def action_draft_user_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def action_draft(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'approver_user_id': False,
            'approved_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def _check_line_unlink(self):
        """
        Check wether a line can be deleted or not.

        Lines cannot be deleted if the status is Approved and Paid or Reimbursed
        :returns: set of lines that cannot be deleted
        """
        return self.filtered(lambda line: line.state in ('validate', 'paid', 'direct_paid', 'reimbursed'))

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove a request that is already Approved or Paid or Reimbursed.'))
        return super(ShipmentExpensePortCharge, self).unlink()

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class ShipmentExpenseTrucking(models.Model):
    _name = "shipment.expense.trucking"
    _order = 'shipment_id, sequence, id'
    _description = "Shipment Expense line for Trucking"
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
    shipment_id = fields.Many2one('operation.shipment', ondelete='cascade')
    description = fields.Char()
    qty = fields.Float(default=1.0, tracking=True, string="QTY")
    uom_id = fields.Many2one('uom.unit', string="UOM", default=lambda self: self.env['uom.unit'].search([('id', '=', 77)]))
    unit_price = fields.Float(tracking=True, copy=False)
    sub_total = fields.Float(store=True, compute="_compute_subtotal_amount", tracking=True, copy=False)
    company_id = fields.Many2one(related='shipment_id.company_id', store=True, readonly=True, default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="cascade",
        domain="[('deprecated', '=', False),('user_type_id.type', 'not in', ('receivable', 'payable')),('is_off_balance', '=', False),(('user_type_id', '=', 17))]",
        check_company=True,
        tracking=True)
    state = fields.Selection([
        ('draft', 'To Confirm'),
        ('confirm', 'To Approve'),
        ('validate', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
        ('direct_paid', 'Direct Paid'),
        ('reimbursed', 'Reimbursed'),
        ], string='Status', default='draft', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Confirm', when request is created." +
        "\nThe status is 'To Approve', when request is checked by user." +
        "\nThe status is 'Approved', when request is approved by user." +
        "\nThe status is 'Paid', when request is paid by user." +
        "\nThe status is 'Direct Paid', bypass Confirm, Validate, and Approve state by user." +
        "\nThe status is 'Reimbursed', when any expenses are not company actual expenses. Subtotal will be zero")
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
    reason = fields.Text(string="Reason", readonly=True, copy=False)
    remark_expense = fields.Char(string="Remark", copy=False)
    clear_advance = fields.Boolean(default=False, string='Clear Advance?', copy=False, readonly=True)
    container_id = fields.Many2one('shipment.container', string="Container No.", ondelete='restrict' , domain="[('shipment_id', '=', shipment_id)]", tracking=True,)

    @api.model
    def default_get(self, fields):
        res = super(ShipmentExpenseTrucking, self).default_get(fields)
        # It seems to be a bug in native odoo that the field partner_id or other many2one
        # fields are not in the fields list by default. A workaround is required
        # to force this. So
        if "default_shipment_id" in self._context and "shipment_id" not in fields:
            fields.append("shipment_id")
            res["shipment_id"] = self._context.get("default_shipment_id")
        return res

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

    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'shipment.expense.trucking'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'shipment.expense.trucking'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'shipment.expense.trucking', 'default_res_id': self.id}
        return res

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
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to confirm this!'))
        if self.filtered(lambda request: request.state != 'draft'):
            raise UserError(_('Request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm', 'checked_user_id': self.env.user.id, 'checked_date': datetime.datetime.today()})
        return True

    def action_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'validate', 'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today()})
        return True

    def action_confirm_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'draft' for request in self):
            raise UserError(_('Expense Line must be Draft in order to Approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'draft').write({
            'state': 'validate',
            'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today(),
            'checked_user_id': current_user.id, 'checked_date':datetime.datetime.today(),
            })
        return True

    def action_reject(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to reject this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to reject it.'))
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'reject'})
        return True

    def action_draft_user_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def action_draft(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'approver_user_id': False,
            'approved_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def _check_line_unlink(self):
        """
        Check wether a line can be deleted or not.

        Lines cannot be deleted if the status is Approved and Paid or Reimbursed
        :returns: set of lines that cannot be deleted
        """
        return self.filtered(lambda line: line.state in ('validate', 'paid', 'direct_paid', 'reimbursed'))

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove a request that is already Approved or Paid or Reimbursed.'))
        return super(ShipmentExpenseTrucking, self).unlink()

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class ShipmentExpenseOtherAdmin(models.Model):
    _name = "shipment.expense.other.admin"
    _order = 'shipment_id, sequence, id'
    _description = "Shipment Expense line for Other Admin Expenses"
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
    shipment_id = fields.Many2one('operation.shipment', ondelete='cascade')
    description = fields.Char()
    qty = fields.Float(default=1.0, tracking=True, string="QTY")
    uom_id = fields.Many2one('uom.unit', string="UOM", default=lambda self: self.env['uom.unit'].search([('id', '=', 77)]))
    unit_price = fields.Float(tracking=True, copy=False)
    sub_total = fields.Float(store=True, compute="_compute_subtotal_amount", tracking=True, copy=False)
    company_id = fields.Many2one(related='shipment_id.company_id', store=True, readonly=True, default=lambda self: self.env.company)
    account_id = fields.Many2one('account.account', string='Account',
        index=True, ondelete="cascade",
        domain="[('deprecated', '=', False),('user_type_id.type', 'not in', ('receivable', 'payable')),('is_off_balance', '=', False),(('user_type_id', '=', 17))]",
        check_company=True,
        tracking=True)
    state = fields.Selection([
        ('draft', 'To Confirm'),
        ('confirm', 'To Approve'),
        ('validate', 'Approved'),
        ('reject', 'Rejected'),
        ('paid', 'Paid'),
        ('direct_paid', 'Direct Paid'),
        ('reimbursed', 'Reimbursed'),
        ], string='Status', default='draft', store=True, tracking=True, copy=False, readonly=False,
        help="The status is set to 'To Confirm', when request is created." +
        "\nThe status is 'To Approve', when request is checked by user." +
        "\nThe status is 'Approved', when request is approved by user." +
        "\nThe status is 'Paid', when request is paid by user." +
        "\nThe status is 'Direct Paid', bypass Confirm, Validate, and Approve state by user." +
        "\nThe status is 'Reimbursed', when any expenses are not company actual expenses. Subtotal will be zero")
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
    reason = fields.Text(string="Reason", readonly=True, copy=False)
    remark_expense = fields.Char(string="Remark", copy=False)
    clear_advance = fields.Boolean(default=False, string='Clear Advance?', copy=False, readonly=True)

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

    attachment_number = fields.Integer('Number of Attachments', compute='_compute_attachment_number')
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'shipment.expense.other.admin'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'shipment.expense.other.admin'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'shipment.expense.other.admin', 'default_res_id': self.id}
        return res

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
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to confirm this!'))
        if self.filtered(lambda request: request.state != 'draft'):
            raise UserError(_('Request must be in Draft state ("To Submit") in order to confirm it.'))
        self.write({'state': 'confirm', 'checked_user_id': self.env.user.id, 'checked_date': datetime.datetime.today()})
        return True

    def action_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'validate', 'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today()})
        return True

    def action_confirm_approve(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to approve this!'))
        if any(request.state != 'draft' for request in self):
            raise UserError(_('Expense Line must be Draft in order to Approve it.'))
        current_user = self.env.user
        self.filtered(lambda request: request.state == 'draft').write({
            'state': 'validate',
            'approver_user_id': current_user.id, 'approved_date':datetime.datetime.today(),
            'checked_user_id': current_user.id, 'checked_date':datetime.datetime.today(),
            })
        return True

    def action_reject(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to reject this!'))
        if any(request.state != 'confirm' for request in self):
            raise UserError(_('Expense Line must be confirmed ("To Approve") in order to reject it.'))
        self.filtered(lambda request: request.state == 'confirm').write({'state': 'reject'})
        return True

    def action_draft_user_confirm(self):
        is_user_confirm = self.env.user.has_group('devel_logistic_management.group_dvl_operation_confirm_expense') or self.env.is_superuser()
        if not is_user_confirm:
            raise UserError(_('You must have user confirm rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def action_draft(self):
        is_manager = self.env.user.has_group('devel_logistic_management.group_dvl_operation_manager') or self.env.is_superuser()
        if not is_manager:
            raise UserError(_('You must have manager rights to do this action!'))
        self.write({
            'state': 'draft',
            'checked_user_id': False,
            'checked_date': False,
            'approver_user_id': False,
            'approved_date': False,
            'move_id': self.move_id.with_context(force_delete=True).unlink(),
            'clear_advance': False
        })
        self._compute_subtotal_amount()
        return True

    def _check_line_unlink(self):
        """
        Check wether a line can be deleted or not.

        Lines cannot be deleted if the status is Approved and Paid or Reimbursed
        :returns: set of lines that cannot be deleted
        """
        return self.filtered(lambda line: line.state in ('validate', 'paid', 'direct_paid', 'reimbursed'))

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove a request that is already Approved or Paid or Reimbursed.'))
        return super(ShipmentExpenseOtherAdmin, self).unlink()

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)