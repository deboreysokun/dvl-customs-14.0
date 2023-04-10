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

from datetime import date
from odoo import api, fields, models, _


class StorageDemurrageCharge(models.Model):
    _name = "storage.demurrage.charge"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Storage And Demurrage Charge by Container Type"

    name = fields.Char(string="Container Type")
    storage_price = fields.Float(string="Storage Charge",tracking=True)
    storage_day_free = fields.Integer(tracking=True, help="#Days Free of Storage Charge")
    demurrage_9day_price = fields.Float(string="1st Demurrage Charge",tracking=True)
    demurrage_9day_day_free = fields.Integer(tracking=True)
    demurrage_over_9day_price = fields.Float(string="2nd Demurrage Charge",tracking=True)
    demurrage_over_9day_day_free = fields.Integer(tracking=True)
    standby_price = fields.Float(string="Standby Charge",tracking=True)
    standby_day_free = fields.Integer(tracking=True)
    detention_price = fields.Float(string="Detention charge",tracking=True)
    detention_day_free = fields.Integer(tracking=True)
    #field customs_penalty_price moves to operation.shipment model
    customs_penalty_day_free = fields.Integer(tracking=True)
