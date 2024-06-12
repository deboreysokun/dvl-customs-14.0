from odoo import fields, api, models


class AccountPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _default_receivable_account(self):
        type_obj = self.env["account.account"]
        company_id = self.env.context.get("company_id") or self.env.company.id
        receivable = type_obj.search(
            [("company_id", "=", company_id),
             ("user_type_id", "like", "%Receivable")], order='code asc')
        return receivable

    @api.model
    def _default_payable_account(self):
        type_obj = self.env["account.account"]
        company_id = self.env.context.get("company_id") or self.env.company.id
        payable = type_obj.search(
            [("company_id", "=", company_id),
             ("name", "like", "%Account Payables")]
        )
        return payable

    property_account_receivable_id = fields.Many2one('account.account', company_dependent=True,
                                                     string="Account Receivable",
                                                     domain="[('internal_type', '=', 'receivable'), ('deprecated', '=', False)]",
                                                     default=_default_receivable_account,
                                                     help="This account will be used instead of the default one as the receivable account for the current partner",
                                                     required=True)
    property_account_payable_id = fields.Many2one('account.account', company_dependent=True,
                                                  string="Account Payable",
                                                  default=_default_payable_account,
                                                  domain="[('internal_type', '=', 'payable'), ('deprecated', '=', False)]",
                                                  help="This account will be used instead of the default one as the payable account for the current partner",
                                                  required=True)