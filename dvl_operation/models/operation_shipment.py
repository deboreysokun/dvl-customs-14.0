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
import base64
import datetime
from datetime import date, timedelta
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from odoo.tools import pdf
from odoo.modules.module import get_module_resource
from odoo.tools.misc import format_datetime

class dvl_operation(models.Model):
    _inherit = 'operation.shipment'

    # Get all Total Invoice for Revenue, Reimburse, Pay Reimburse
    total_all_invoices = fields.Monetary(currency_field='company_currency_id', string="Total All", compute='_total_all_invoices', groups='account.group_account_invoice,account.group_account_readonly')
    all_invoice_ids = fields.One2many(string='Related Invoices', inverse_name='shipment_id', comodel_name='account.move', domain=[('state', '=', 'posted')])

    def _total_all_invoices(self):
        for record in self:
            record.total_all_invoices = 0
            if not self.ids:
                return True
            domain = [
                ('shipment_id', '=', record.id),
                ('state', 'not in', ['cancel']),
                ('move_type', 'in', ('out_invoice', 'out_refund','in_invoice', 'in_refund')),
                # ('journal_id.is_reimbursement', '=', False), # excluded reimbursement journal
            ]
            price_totals = self.env['account.move'].read_group(domain, ['amount_total_signed'], ['shipment_id'])
            record.total_all_invoices = sum(amount['amount_total_signed'] for amount in price_totals)

    def action_view_total_all_invoices(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action['domain'] = [
            ('shipment_id', '=', self.id),
            ('state', 'not in', ['cancel']),
            ('move_type', 'in', ('out_invoice', 'out_refund','in_invoice', 'in_refund')),
            # ('journal_id.is_reimbursement', '=', False), # excluded reimbursement journal
        ]
        if self.operation_type == 'import':
            journal_id = self.env['account.journal'].search([('name', 'ilike', 'Import')], limit=1)
        elif self.operation_type == 'export':
            journal_id = self.env['account.journal'].search([('name', 'ilike', 'Export')], limit=1)
        else:
            journal_id = self.env['account.journal'].search([('name', 'ilike', 'Transit')], limit=1)
        action['context'] = {
            'default_move_type': 'out_invoice out_refund in_invoice in_refund',
            'default_shipment_id': self.id,
            # 'default_partner_id': self.id,
            'default_journal_id': journal_id.id,
        }
        return action


