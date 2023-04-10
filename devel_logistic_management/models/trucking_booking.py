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

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class TruckBooking(models.Model):
    _name = "truck.booking"
    _order = "name desc, booking_date desc"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Truck Booking"
    _check_company_auto = True

    company_id = fields.Many2one(comodel_name='res.company',default=lambda self: self.env.company)

    active = fields.Boolean('Active', compute="_compute_active" , default=True, store=True,tracking=True)
    name = fields.Char(string="Booking N0.", default=lambda self: _('New'),
                copy=False, readonly=True)
    booking_date = fields.Date(default=fields.Date.context_today, tracking=True,)
    shipment_id = fields.Many2one('operation.shipment', string="Shipmet N0.", tracking=True,)
    bl_number = fields.Char(related='shipment_id.bl_number')
    truck_type = fields.Many2one('truck.type', tracking=True)
    truck_number = fields.Char(tracking=True,)
    trailer_number = fields.Char(string="Trailer N0.", tracking=True,)
    driver_id = fields.Many2one('truck.company.driver', ondelete='restrict' ,domain="[('truck_partner_id', '=', truck_partner_id)]", tracking=True,)
    driver_number = fields.Char(related='driver_id.driver_number', tracking=True,)
    director_name = fields.Char(related='truck_partner_id.director_name', string="Director", tracking=True,)
    director_number = fields.Char(related='truck_partner_id.director_phone', tracking=True,)
    truck_partner_id = fields.Many2one('res.partner', string="Company", tracking=True)
    truck_company_phone = fields.Char(related='truck_partner_id.phone', string="Company Phone", tracking=True,)
    truck_company_address = fields.Char(related='truck_partner_id.street', string="Address", tracking=True,)

    pick_up_empty_location_id = fields.Many2one('truck.location', copy="True", tracking=True)
    pick_up_date = fields.Date(tracking=True,)

    release_empty_location_id = fields.Many2one('truck.location', copy="True", tracking=True)
    release_date = fields.Date(tracking=True,)

    loading_location_id = fields.Many2one('truck.location', copy="True", tracking=True)
    loading_date = fields.Date(tracking=True,)

    delivery_location_id = fields.Many2one('truck.location', copy="True", tracking=True)
    delivery_date = fields.Date(tracking=True,)

    note = fields.Text(tracking=True,)
    container_id = fields.Many2one('shipment.container', string="Container No.", ondelete='restrict' ,domain="[('shipment_id', '=', shipment_id)]", tracking=True,)
    container_seal_id = fields.Char(string="Seal No.", related='container_id.container_seal_number', copy=False, tracking=True,)

    #These fields are related fields of shipment Container
    number_standby_days = fields.Integer('#Days Standby', compute="_compute_standby_charge")
    standby_charge = fields.Monetary(readonly=True,currency_field='currency_id', compute="_compute_standby_charge")
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id')

    have_product = fields.Boolean('Have Products?', help='Indicated that container has products', tracking=True)
    operation_type = fields.Selection(selection =[
            ('import', 'Import'),
            ('export', 'Export'),
            ('transit', 'Transit'),
            ('other', 'Other')],
            string='Type', tracking=True)

    @api.depends('shipment_id.active')
    def _compute_active(self):
        for trucking in self:
            trucking.active = True
            if trucking.shipment_id:
                trucking.active = trucking.shipment_id.active


    @api.onchange('container_id.number_standby_days', 'container_id.standby_charge')
    def _compute_standby_charge(self):
        for line in self:
            line.standby_charge = line.container_id.standby_charge
            line.number_standby_days = line.container_id.number_standby_days

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('new')) == _('new'):
            vals['name'] = self.env['ir.sequence'].next_by_code('truck.booking') or _('new')
        result = super(TruckBooking, self).create(vals)
        return result

    @api.onchange('shipment_id')
    def _onchange_shipment_id(self):
        if self.shipment_id and self.shipment_id != self.container_id.shipment_id:
            self.container_id = False
            self.container_seal_id = False

    @api.onchange('truck_partner_id')
    def _onchange_truck_partner_id(self):
        if self.truck_partner_id and self.truck_partner_id != self.driver_id.truck_partner_id:
            self.driver_id = False

    @api.model
    def default_get(self, fields):
        res = super(TruckBooking, self).default_get(fields)
        # It seems to be a bug in native odoo that the field partner_id or other many2one
        # fields are not in the fields list by default. A workaround is required
        # to force this. So
        if "default_shipment_id" in self._context and "shipment_id" not in fields:
            fields.append("shipment_id")
            res["shipment_id"] = self._context.get("default_shipment_id")
        return res

    def unlink(self):
        for record in self:
            raise UserError(_('You can not delete this record. Please archive it instead.'))
        return super(TruckBooking, self).unlink()

class TruckCompanyDriver(models.Model):
    _name = "truck.company.driver"
    _description = "Truck Driver of Company"
    _rec_name = 'driver_name'

    truck_partner_id = fields.Many2one('res.partner', tracking=True)
    driver_name = fields.Char(string="Driver", tracking=True,)
    driver_number = fields.Char(string="Phone Number", tracking=True,)

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class TruckType(models.Model):
    _name = "truck.type"
    _description = "Type of Truck or Vehicle"

    name = fields.Char()

class TruckLocation(models.Model):
    _name = "truck.location"
    _description = "Place or Location"

    name = fields.Char()
