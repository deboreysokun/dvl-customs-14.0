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
import datetime
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError

class ShipmentCoverTemplate(models.Model):
    _name = "shipment.cover.template"
    _description = "Shipment Cover Template"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    company_id = fields.Many2one(comodel_name='res.company', string='Company',default=lambda self: self.env.company)

    name = fields.Char()
    note = fields.Text('Terms and conditions')

    shipment_id = fields.Many2one(comodel_name="operation.shipment")
    checking_list_shipment_ids = fields.One2many('checking.list.shipment.template.line', 'checking_list_shipment_id', copy=True)
    process_list_shipment_ids = fields.One2many('process.list.shipment.template.line', 'process_list_shipment_id', copy=True)
    cash_payment_shipment_ids = fields.One2many('cash.payment.shipment.template.line', 'cash_payment_shipment_id', copy=True)

class CheckingListShipmentTemplate(models.Model):
    _name = "checking.list.shipment.template.line"
    _order = 'checking_list_shipment_id, sequence, id'
    _description = "Checking List Shipment Cover Template Line"

    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of lines.",default=10)
    checking_list_shipment_id = fields.Many2one('shipment.cover.template', required=True, ondelete='cascade', index=True)
    name = fields.Char("Description")
    display_type = fields.Selection([
            ('line_section', "Title"),
            ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

class ProcessListShipmentTemplate(models.Model):
    _name = "process.list.shipment.template.line"
    _order = 'process_list_shipment_id, sequence, id'
    _description = "Process List Shipment Cover Template Line"

    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of lines.",default=10)
    process_list_shipment_id = fields.Many2one('shipment.cover.template', required=True, ondelete='cascade', index=True)
    name = fields.Char("Description")
    display_type = fields.Selection([
            ('line_section', "Title"),
            ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

class CashPaymentShipmentTemplate(models.Model):
    _name = "cash.payment.shipment.template.line"
    _order = 'cash_payment_shipment_id, sequence, id'
    _description = "Cash Payment Request Shipment Template Line"

    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of lines.",default=10)
    cash_payment_shipment_id = fields.Many2one('shipment.cover.template', required=True, ondelete='cascade', index=True)
    name = fields.Char("Description")
    uom_id = fields.Many2one('uom.unit', string="UOM")
    display_type = fields.Selection([
            ('line_section', "Title"),
            ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
