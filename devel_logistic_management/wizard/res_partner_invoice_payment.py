from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _

class ResPartnerInvoicePayment(models.TransientModel):
    _name = 'res.partner.invoice.payment'

    start_date = fields.Date(string="Start Date", required=True,
        default=lambda self: fields.Date.today().replace(day=1) - relativedelta(days=30))
    end_date = fields.Date(string="End Date", required=True,
        default=lambda self: fields.Date.today())
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
        default=lambda self: self.env.company)

    def print_invoice_payment_history(self):
        data = {
            "ids": self.ids,
            "model": 'res.partner',
            "partner_ids": self._context["active_ids"],
            "start_date": self.start_date,
            "end_date": self.end_date,
            "company_id": self.company_id.id,
        }
        return self.env.ref('devel_logistic_management.action_partner_invoice_payment').report_action(self.ids, data=data)

class ResPartnerShipmentInvoice(models.TransientModel):
    _name = 'res.partner.shipment.invoice'

    start_date = fields.Date(string="Start Date", required=True,
        default=lambda self: fields.Date.today().replace(day=1) - relativedelta(days=30))
    end_date = fields.Date(string="End Date", required=True,
        default=lambda self: fields.Date.today())
    company_id = fields.Many2one(comodel_name='res.company', string='Company',
        default=lambda self: self.env.company)

    def print_shipment_invoice_status(self):
        data = {
            "ids": self.ids,
            "model": 'res.partner',
            "partner_ids": self._context["active_ids"],
            "start_date": self.start_date,
            "end_date": self.end_date,
            "company_id": self.company_id.id,
        }
        return self.env.ref('devel_logistic_management.action_partner_shipment_invoice_status').report_action(self.ids, data=data)
