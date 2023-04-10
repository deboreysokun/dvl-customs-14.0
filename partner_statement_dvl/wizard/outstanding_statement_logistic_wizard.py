# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class OutstandingStatementLogisticWizard(models.TransientModel):
    """Outstanding Statement Logistic wizard."""

    _name = "outstanding.statement.logistic.wizard"
    _inherit = "statement.common.wizard"
    _description = "Outstanding Statement Logistci Wizard"

    def _export(self):
        """Export to PDF."""
        data = self._prepare_statement()
        return self.env.ref("partner_statement_dvl.action_print_outstanding_statement_logistic").report_action(self.ids, data=data)
