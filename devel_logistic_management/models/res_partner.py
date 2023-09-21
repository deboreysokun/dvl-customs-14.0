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
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class Partner(models.Model):
    _inherit = 'res.partner'

    fax = fields.Char(tracking=True)
    khmer_name = fields.Char(string="Khmer Name", copy=False, tracking=True)
    signature_image = fields.Image(copy=False, tracking=True)
    id_card_number = fields.Char(copy=False, tracking=True)
    id_card_date = fields.Date(tracking=True)
    id_card_front_image = fields.Image(copy=False, tracking=True)
    id_card_back_image = fields.Image(copy=False, tracking=True)
    vattin_date = fields.Date(string="VAT Date", tracking=True)
    patent_number = fields.Char(tracking=True)
    patent_date = fields.Date(tracking=True)
    business_activities = fields.Char(help="សម្មភាពអាជីវកម្ម",tracking=True)
    # kh_name = fields.Char(string="Khmer Name", copy=False, tracking=True)
    # eng_name = fields.Char(string="English Name", copy=False, tracking=True)
    gender = fields.Selection(
        [("male", "Male"), ("female", "Female"), ("other", "Other")], tracking=True
    )
    nationality_id = fields.Many2one("res.country", "Nationality", tracking=True)
    birthdate_date = fields.Date("Birthdate", tracking=True)
    age = fields.Integer(string="Age", readonly=True, compute="_compute_age", tracking=True)

    cb_card_front_image = fields.Image(copy=False, tracking=True, string="CB Card Front", help="ប័ណ្ណសម្គាល់ជើងសារគយ")
    cb_card_back_image = fields.Image(copy=False, tracking=True, string="CB Card Back", help="ប័ណ្ណសម្គាល់ជើងសារគយ")
    cb_card_number = fields.Char(tracking=True, string="CB Card N0.", help="លេខប័ណ្ណសម្គាល់ជើងសារគយ")
    cb_card_date = fields.Date(tracking=True,string="Expire Date")

    emp_card_front_image = fields.Image(copy=False, tracking=True, string="Employee Card Front")
    emp_card_back_image = fields.Image(copy=False, tracking=True, string="Employee Card Back")
    emp_card_number = fields.Char(tracking=True, string="Employee Card N0.")
    emp_card_date = fields.Date(tracking=True,string="Expire Date")

    mocid = fields.Char(string="MOCID", help="Certificate of Incorporation", tracking=True)
    mocid_date = fields.Date(tracking=True)

    total_shipments_count = fields.Integer(compute='_shipment_count', string="All Shipments",
        groups='account.group_account_invoice,account.group_account_readonly')
    shipments_no_invoice_count = fields.Integer(compute='_shipment_count', string="Shipment Not Yet Issued Invoices",
        groups='account.group_account_invoice,account.group_account_readonly')

    @api.depends("birthdate_date")
    def _compute_age(self):
        for record in self:
            age = 0
            if record.birthdate_date:
                age = relativedelta(fields.Date.today(), record.birthdate_date).years
            record.age = age

    # Fields for the partner when it acts as an Truck Company
    is_truck = fields.Boolean(
        string="Truck Company",
        help="Check this field if the partner is a truck company.",
    )
    director_name = fields.Char(string="Director", tracking=True)
    director_phone = fields.Char(string="Director Phone", tracking=True)
    driver_ids = fields.One2many('truck.company.driver', 'truck_partner_id')

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def _get_name(self):
        name = super(Partner, self)._get_name()
        if self._context.get('show_mobile'):
            if self.mobile and not self.phone:
                name += "\n" + "%s" % (self.mobile or '')
            if self.phone and not self.mobile:
                name += "\n" + "%s" % (self.phone or '')
            if self.mobile and self.phone:
                name += "\n" + "%s / %s" % (self.phone or '', self.mobile or '')
        return name

    def _shipment_count(self):
        for partner in self:
            partner.shipments_no_invoice_count = 0
            partner.total_shipments_count = 0
            if not partner.ids:
                return True
            shipment_no_invoice = self.env['operation.shipment'].search([
                ('customer_id', '=', self.id), ('issued_invoice_date' , '=', False)])
            partner.shipments_no_invoice_count = len(shipment_no_invoice)

            all_shipments = self.env['operation.shipment'].search([
                ('customer_id', '=', self.id)])
            partner.total_shipments_count = len(all_shipments)

    def action_view_partner_shipments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("devel_logistic_management.action_dvl_operation_all")
        action['domain'] = [
            ('customer_id', 'child_of', self.id)
        ]
        action['context'] = {'default_customer_id': self.id, 'search_default_no_invoice_date': 1}
        return action

class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    #Client need it
    street = fields.Char(string="Account Address")
