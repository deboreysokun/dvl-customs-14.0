# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models,fields


class OutstandingStatementLogisticWizard(models.TransientModel):
    """Outstanding Statement Logistic wizard."""

    _name = "outstanding.statement.logistic.wizard"
    _inherit = "statement.common.wizard"
    _description = "Outstanding Statement Logistci Wizard"
    customer_id = fields.Many2one('res.partner', tracking=True)
    agent_staff_id = fields.Many2one(
        comodel_name='res.partner.agent.staff',
    )

    def _prepare_statement(self):
        data = super()._prepare_statement()
        # Add customer_id and agent_staff_id to the data dictionary
        data.update({
            'customer_id': self.customer_id.id if self.customer_id else False,
            'agent_staff_id': self.agent_staff_id.id if self.agent_staff_id else False,
        })
        return data
    def _export(self):
        """Export to PDF."""
        data = self._prepare_statement()
        return self.env.ref("partner_statement_dvl.action_print_outstanding_statement_logistic").report_action(self.ids, data=data)
