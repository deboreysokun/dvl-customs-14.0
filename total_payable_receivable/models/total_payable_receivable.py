# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: odoo@cybrosys.com
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, models, fields


class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    partner_credit = fields.Monetary(compute='credit_debit_get',string='Total Receivable', compute_sudo=True, help="Total amount this customer owes you.")
    partner_debit = fields.Monetary(compute='credit_debit_get',string='Total Payable', compute_sudo=True, help="Total amount you have to pay to this vendor.")
    # new added
    entry_debit_credit = fields.Monetary(compute='credit_debit_get',string='Total Entries', compute_sudo=True)

    @api.depends_context('force_company')
    def credit_debit_get(self):
        partner_debit = 0.0
        partner_credit = 0.0
        entry_debit_credit = 0.0
        tables, where_clause, where_params = self.env['account.move.line'].with_context(state='posted', company_id=self.env.company.id)._query_get()
        where_params = [tuple(self.ids)] + where_params
        if where_clause:
            where_clause = 'AND ' + where_clause
        self._cr.execute("""SELECT account_move_line.partner_id, act.type, SUM(account_move_line.amount_residual)

                      FROM """ + tables + """
                      LEFT JOIN account_account a ON (account_move_line.account_id=a.id)
                      LEFT JOIN account_account_type act ON (a.user_type_id=act.id)
                      WHERE act.type IN ('receivable','payable','liquidity')
                      AND account_move_line.partner_id IN %s
                      AND account_move_line.reconciled IS FALSE
                      """ + where_clause + """
                      GROUP BY account_move_line.partner_id, act.type
                      """, where_params)
        treated = self.browse()
        for pid, type, val in self._cr.fetchall():
            partner = self.browse(pid)
            if type == 'receivable':
                partner.partner_credit = val
                partner_credit = partner.partner_credit
                partner.partner_debit = False
                treated |= partner
            elif type == 'payable':
                partner.partner_debit = -val
                partner_debit = partner.partner_debit
                partner.partner_credit = False
                treated |= partner
            elif type == 'liquidity':
                partner.entry_debit_credit = val
                entry_debit_credit = partner.entry_debit_credit
                treated |= partner
        remaining = (self - treated)
        self.partner_debit = partner_debit
        self.entry_debit_credit = entry_debit_credit
        self.partner_credit = partner_credit
        remaining.partner_debit = False
        remaining.partner_credit = False

    # new added
    def action_view_expense_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("total_payable_receivable.action_view_partner_account_move_line")
        return action

