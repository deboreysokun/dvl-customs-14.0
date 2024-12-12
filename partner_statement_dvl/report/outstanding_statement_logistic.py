# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class OutstandingStatementLogistic(models.AbstractModel):
    """Model of Outstanding Statement Of Logistic Operation"""

    _inherit = "statement.common"
    _name = "report.partner_statement_dvl.outstanding_statement_logistic"
    _description = "Partner Outstanding Statement of Logistic Operation"

    def _display_lines_sql_q1(self, partners, date_end, account_type):
        partners = tuple(partners)
        return str(
            self._cr.mogrify(
                """
            SELECT l.id, m.name AS move_id, l.partner_id, l.date, l.name,
                            l.blocked, l.currency_id, l.company_id,
                            op.name AS shipment_id, op.operation_type, op.bl_number, op.container_number, op.commodity, pod.name AS port_of_delivery, pol.name AS port_of_loading,
                            pod1.name AS port_of_discharge, fd.name AS final_destination, por.name AS place_of_reciept, op.etd, op.eta, op.etr, incoterm.code AS incoterm_id, inv_inco.code AS inv_packing_list_term,
            CASE WHEN l.ref IS NOT NULL
                THEN l.ref
                ELSE m.ref
            END as ref,
            CASE WHEN (l.currency_id is not null AND l.amount_currency > 0.0)
                THEN avg(l.amount_currency)
                ELSE avg(l.debit)
            END as debit,
            CASE WHEN (l.currency_id is not null AND l.amount_currency < 0.0)
                THEN avg(l.amount_currency * (-1))
                ELSE avg(l.credit)
            END as credit,
            CASE WHEN l.balance > 0.0
                THEN l.balance - sum(coalesce(pd.amount, 0.0))
                ELSE l.balance + sum(coalesce(pc.amount, 0.0))
            END AS open_amount,
            CASE WHEN l.balance > 0.0
                THEN l.amount_currency - sum(coalesce(pd.debit_amount_currency, 0.0))
                ELSE l.amount_currency + sum(coalesce(pc.credit_amount_currency, 0.0))
            END AS open_amount_currency,
            CASE WHEN l.date_maturity is null
                THEN l.date
                ELSE l.date_maturity
            END as date_maturity
            FROM account_move_line l
            JOIN account_account aa ON (aa.id = l.account_id)
            JOIN account_account_type at ON (at.id = aa.user_type_id)
            JOIN account_move m ON (l.move_id = m.id)
            LEFT JOIN operation_shipment op ON (op.id = m.shipment_id)
            LEFT JOIN entry_exit_port pod ON (pod.id = op.port_of_delivery)
            LEFT JOIN entry_exit_port pod1 ON (pod1.id = op.port_of_discharge_report)
            LEFT JOIN entry_exit_port pol ON (pol.id = op.port_of_loading_report)
            LEFT JOIN entry_exit_port fd ON (fd.id = op.final_destination)
            LEFT JOIN entry_exit_port por ON (por.id = op.place_of_reciept)
            LEFT JOIN account_incoterms incoterm ON (incoterm.id = op.incoterm_id)
            LEFT JOIN account_incoterms inv_inco ON (inv_inco.id = op.inv_packing_list_term)
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.credit_move_id = l2.id
                WHERE l2.date <= %(date_end)s
            ) as pd ON pd.debit_move_id = l.id
            LEFT JOIN (SELECT pr.*
                FROM account_partial_reconcile pr
                INNER JOIN account_move_line l2
                ON pr.debit_move_id = l2.id
                WHERE l2.date <= %(date_end)s
            ) as pc ON pc.credit_move_id = l.id
            WHERE l.partner_id IN %(partners)s AND at.type = %(account_type)s
                                AND (
                                  (pd.id IS NOT NULL AND
                                      pd.max_date <= %(date_end)s) OR
                                  (pc.id IS NOT NULL AND
                                      pc.max_date <= %(date_end)s) OR
                                  (pd.id IS NULL AND pc.id IS NULL)
                                ) AND l.date <= %(date_end)s AND m.state IN ('posted')
            GROUP BY l.id, l.partner_id, m.name, l.date, l.date_maturity, l.name,
                op.name, op.operation_type, op.bl_number, op.container_number, op.commodity, pod.name, pol.name, pod1.name, fd.name, por.name, op.etd, op.eta, op.etr, incoterm.code, inv_inco.code,
                CASE WHEN l.ref IS NOT NULL
                    THEN l.ref
                    ELSE m.ref
                END,
                l.blocked, l.currency_id, l.balance, l.amount_currency, l.company_id
            """,
                locals(),
            ),
            "utf-8",
        )

    def _display_lines_sql_q2(self):
        return str(
            self._cr.mogrify(
                """
                SELECT Q1.partner_id, Q1.currency_id, Q1.move_id,
                    Q1.date, Q1.date_maturity, Q1.debit, Q1.credit,
                    Q1.name, Q1.ref, Q1.blocked, Q1.company_id,
                    Q1.shipment_id, Q1.operation_type, Q1.bl_number, Q1.container_number, Q1.commodity, Q1.port_of_delivery, Q1.port_of_loading,
                    Q1.port_of_discharge, Q1.final_destination, Q1.place_of_reciept, Q1.etd, Q1.eta, Q1.etr, Q1.incoterm_id, Q1.inv_packing_list_term,
                CASE WHEN Q1.currency_id is not null
                    THEN Q1.open_amount_currency
                    ELSE Q1.open_amount
                END as open_amount
                FROM Q1
                """,
                locals(),
            ),
            "utf-8",
        )

    def _display_lines_sql_q3(self, company_id):
        return str(
            self._cr.mogrify(
                """
            SELECT Q2.partner_id, Q2.move_id, Q2.date, Q2.date_maturity,
              Q2.name, Q2.ref, Q2.debit, Q2.credit,
              Q2.debit-Q2.credit AS amount, blocked,
              Q2.shipment_id, Q2.operation_type, Q2.bl_number, Q2.container_number, Q2.commodity, Q2.port_of_loading, Q2.port_of_delivery,
              Q2.port_of_discharge, Q2.final_destination, Q2.place_of_reciept, Q2.etd, Q2.eta, Q2.etr, Q2.incoterm_id, Q2.inv_packing_list_term,
              COALESCE(Q2.currency_id, c.currency_id) AS currency_id,
              Q2.open_amount
            FROM Q2
            JOIN res_company c ON (c.id = Q2.company_id)
            WHERE c.id = %(company_id)s AND Q2.open_amount != 0.0
            """,
                locals(),
            ),
            "utf-8",
        )

    def _get_account_display_lines(self, company_id, partner_ids, date_start, date_end, account_type):
        res = dict(map(lambda x: (x, []), partner_ids))
        partners = tuple(partner_ids)
        # pylint: disable=E8103
        self.env.cr.execute(
            """
        WITH Q1 as (%s),
             Q2 AS (%s),
             Q3 AS (%s)
        SELECT partner_id, currency_id, move_id, date, date_maturity, debit,
                            credit, amount, open_amount, name, ref, blocked,
                            shipment_id, operation_type, bl_number, container_number, commodity, port_of_loading, port_of_delivery, port_of_discharge, final_destination, place_of_reciept, etd, eta, etr, incoterm_id, inv_packing_list_term
        FROM Q3
        ORDER BY date, date_maturity, move_id, shipment_id, operation_type, bl_number, container_number, commodity, port_of_loading, port_of_delivery, port_of_discharge, final_destination, place_of_reciept, etd, eta, etr, incoterm_id, inv_packing_list_term""" % (
                self._display_lines_sql_q1(partners, date_end, account_type),
                self._display_lines_sql_q2(),
                self._display_lines_sql_q3(company_id)))
        for row in self.env.cr.dictfetchall():
            res[row.pop("partner_id")].append(row)

        for partner_id in res:
            res[partner_id][:] = [
                d for d in res[partner_id]
                if self.env['account.move'].sudo().search([
                    ('name', '=', d.get('move_id')),
                    ('partner_id', '=', partner_id),
                ]).move_type == 'out_invoice'
            ]

            res[partner_id][:] = [
                d for d in res[partner_id]
                if self.env['account.move'].sudo().search([
                    ('name', '=', d.get('move_id')),
                    ('partner_id', '=', partner_id)
                ]).payment_state != 'paid'
            ]

            res[partner_id].sort(key=lambda line: (not line.get("shipment_id", False), line.get("shipment_id")))

            for d in res[partner_id]:
                age = self.env['res.partner.aging.customer'].sudo().search([
                    ('invoice_ref', '=', d.get('move_id')),
                    ('partner_id', '=', partner_id),
                ])[0]
                d['age'] = age.max_days_overdue


        # for partner_id in res:
        #     res[partner_id].sort(key=lambda line: line["shipment_id"])


        return res
    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {}
        if "company_id" not in data:
            wiz = self.env["outstanding.statement.logistic.wizard"].with_context(
                active_ids=docids, model="res.partner"
            )
            data.update(wiz.create({})._prepare_statement())
        data["amount_field"] = "open_amount"
        print('=============', data)
        return super()._get_report_values(docids, data)

