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

from random import randint

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression
from dateutil.relativedelta import relativedelta


class HsCode(models.Model):
    _name = "hs.code"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "head_id asc"
    _description = "Customs Tariff of Cambodia"
    _rec_name = 'tariff_code'

    #_sql_constraints = [('tariff_code_unique', 'unique(tariff_code)', "HS Code must be unique ! Please choose another one.")]
    _sql_constraints = [('tariff_code_unique', 'check(1=1)', 'No error')]

    active = fields.Boolean('Active', default=True, tracking=True, related="year_id.active", store=True)
    year_id = fields.Many2one('hs.code.year', tracking=True)
    head_id = fields.Many2one('head.hs.code', tracking=True)
    tariff_code = fields.Char(help='HS Code e.g: 1704.10.00', copy=False, index=True, tracking=True)
    description_kh = fields.Char('បរិយាយមុខទំនិញ', copy=False, tracking=True)
    description = fields.Char('Description of Goods', copy=False, tracking=True)
    unit_id = fields.Many2one('uom.unit', tracking=True)
    cd = fields.Char(string="CD",help='Customs Duty Tax', copy=False, tracking=True)
    st = fields.Char(string="ST", help='Special Tax',  copy=False, tracking=True)
    vat = fields.Char(string="VAT", help='Value Added Tax',  copy=False, tracking=True)
    et = fields.Char(string="ET", help='Export Tax', copy=False, tracking=True)
    at = fields.Char(string="AT", help='Additional Tax on Petroleum Product', copy=False, tracking=True)
    ministry_info = fields.Text(string="Ministry", tracking=True)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, '%s' % (record.tariff_code)))
        return result

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [('tariff_code', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)


class HeadHsCode(models.Model):
    _name = "head.hs.code"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "head asc"
    _description = "Head Of HS Code"
    _rec_name = 'head'

    head = fields.Char(help='Head of HS Code e.g: 17.04', copy=False, tracking=True)
    year_ids = fields.Many2many('hs.code.year', tracking=True, compute="_get_years")
    head_code_lines = fields.One2many('hs.code', 'head_id')

    def _get_years(self):
        for record in self:
            record.year_ids = record.head_code_lines.mapped('year_id')

class HsCodeYear(models.Model):
    _name = "hs.code.year"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Year Of HS Code"

    name = fields.Char(string="Year")
    description = fields.Char()
    active = fields.Boolean('Active', default=True, tracking=True)
    hs_code_line_ids = fields.One2many('hs.code', 'year_id')

###### Import HS Code line in Hcode Year ####################
class Import(models.TransientModel):
    _inherit = 'base_import.import'

    @api.model
    def _convert_import_data(self, fields, options):
        data,fields=super(Import,self)._convert_import_data(fields,options)
        if self._context.get('import_hscode_item'):
            import_field = options.get('import_field')
            year_id = options.get('year_id')
            if import_field and year_id:
                fields.append(import_field)
                for row in data:
                    row.append(year_id)
        return data,fields

    def do(self, fields, columns, options, dryrun=False):
        return super(Import,self.with_context(dryrun=dryrun,import_hscode_item=options.get('import_hscode_item'))).do(fields,columns,options,dryrun)

class Measurement(models.Model):
    _name = "uom.unit"
    _description = "Measurement"

    name = fields.Char(size=6,help='Unit of Measurement', copy=False, tracking=True,)
    description = fields.Char(copy=False, tracking=True,)

    def _get_name(self):
        record = self
        name = record.name or ''
        if self._context.get('show_full_name') and record.description:
            name = name + " - " + record.description
        return name

    def name_get(self):
        res = []
        for record in self:
            name = record._get_name()
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += ["|", ("name", operator, name), ("description", operator, name)]
        return self.search(domain, limit=limit).name_get()

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class ShipmentType(models.Model):
    _name = "shipment.type"
    _description = "Shipment Type"

    name = fields.Char(help='Shipment Type', copy=False, tracking=True,)
    description = fields.Char(copy=False, tracking=True,)

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class Country(models.Model):
    _inherit = 'res.country'

    khmer_name = fields.Char(tracking=True,)

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class EntryExitPort(models.Model):
    _name = 'entry.exit.port'
    _description = "Entry and Exit Ports"

    name = fields.Char(copy=False, tracking=True,)
    kh_name = fields.Char(string="Khmer Name", copy=False, tracking=True)

    def _get_name(self):
        record = self
        name = record.name or ''
        if self._context.get('show_khmer_name') and record.kh_name:
            name = name + "\n" + record.kh_name
        return name

    def name_get(self):
        res = []
        for record in self:
            name = record._get_name()
            res.append((record.id, name))
        return res

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class ClearanceOffice(models.Model):
    _name = 'clearance.office'
    _description = "Customs Clearance Office"

    name = fields.Char(string='English Name', copy=False, tracking=True,)
    kh_name = fields.Char(string='Khmer Name', copy=False, tracking=True,)
    code = fields.Char(copy=False, tracking=True)

    def _get_name(self):
        record = self
        name = record.name or ''
        if self._context.get('show_khmer_name') and record.kh_name:
            name = name + "\n" + record.kh_name
        return name

    def name_get(self):
        res = []
        for record in self:
            name = record._get_name()
            res.append((record.id, name))
        return res

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class CoForm(models.Model):
    _name = 'co.form'
    _description = "Certificate of Origin Form"
    _rec_name = 'form_type'

    name = fields.Char(help='ឈ្មោះកិច្ចព្រមព្រៀងពាណិជ្ជកម្មសេរី', copy=False, tracking=True,)
    sub_decree = fields.Char(help='អនុក្រឹត្យ/ប្រកាស', copy=False, tracking=True,)
    form_type = fields.Char(help='ប្រភេទ CO', copy=False, tracking=True,)

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def name_get(self):
        res = []
        for co in self:
            name = '%s - %s' % (co.form_type, co.name)
            res.append((co.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += ["|", ("form_type", operator, name), ("name", operator, name)]
        return self.search(domain, limit=limit).name_get()

class HrEmployee(models.Model):
    _inherit = "hr.employee"

    age = fields.Integer(compute="_compute_age", tracking=True,)
    signature = fields.Binary()
    khmer_name = fields.Char(tracking=True)
    id_card_front_image = fields.Image(copy=False, tracking=True)
    id_card_back_image = fields.Image(copy=False , tracking=True)

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    @api.depends("birthday")
    def _compute_age(self):
        for record in self:
            age = 0
            if record.birthday:
                age = relativedelta(fields.Date.today(), record.birthday).years
            record.age = age

class HrEmployeePublic(models.Model):
    _inherit = "hr.employee.public"

    khmer_name = fields.Char()

class ContainerType(models.Model):
    _name = 'container.type'
    _description = 'Container Type'

    name = fields.Char(string='Name', required=True, tracking=True,)
    code = fields.Char(tracking=True,)
    charge_type_id = fields.Many2one('storage.demurrage.charge', string="Container Charge Type")

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def name_get(self):
        res = []
        for container in self:
            name = '%s - %s' % (container.code, container.name)
            res.append((container.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += ["|", ("code", operator, name), ("name", operator, name)]
        return self.search(domain, limit=limit).name_get()

class Consignment(models.Model):
    _name = 'consignment'
    _description = 'E / F Consignment'

    name = fields.Char(string='Name', required=True, tracking=True,)
    code = fields.Char(tracking=True,)

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    def name_get(self):
        res = []
        for consignment in self:
            name = '%s - %s' % (consignment.code, consignment.name)
            res.append((consignment.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += ["|", ("code", operator, name), ("name", operator, name)]
        return self.search(domain, limit=limit).name_get()

class Tag(models.Model):
    _name = "operation.tag"
    _description = "Shipment Operation Tag"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char('Tag Name', required=True, translate=True, tracking=True,)
    color = fields.Integer('Color', default=_get_default_color)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)

class OperationStage(models.Model):
    _name = "operation.stage"
    _description = "Shipment Stages"
    _rec_name = 'name'
    _order = "sequence, name, id"

    name = fields.Char('Stage Name', required=True, translate=True, tracking=True,)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")
    is_done = fields.Boolean('Is Done Stage?')
    requirements = fields.Text('Requirements', help="Enter here the internal requirements for this stage (ex: BL sent to custoemr). It will appear as a tooltip over the stage's name.")
    fold = fields.Boolean('Folded in Pipeline',
        help='This stage is folded in the kanban view when there are no records in that stage to display.')

    def _valid_field_parameter(self, field, name):
        return name == 'tracking' or super()._valid_field_parameter(field, name)


class AccountIncoterms(models.Model):
    _inherit = 'account.incoterms'

    #overwirte to allow 6 charater
    code = fields.Char(
        'Code', size=6, required=True,
        help="Incoterm Standard Code")

    def _get_name(self):
        record = self
        name = record.code or ''
        if self._context.get('show_full_name') and record.name:
            name = name + " - " + record.name
        return name

    def name_get(self):
        res = []
        for record in self:
            name = record._get_name()
            res.append((record.id, name))
        return res

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        domain = args or []
        domain += ["|", ("code", operator, name), ("name", operator, name)]
        return self.search(domain, limit=limit).name_get()

class ProvinceCity(models.Model):
    _name = "province.city"
    _description = 'Provinc in Cambodia'
    _rec_name = 'kh_name'

    name = fields.Char()
    kh_name = fields.Char(string="Khmer Name")

####### These classed are for HSCODE of Type Vehicle #######################
class VehicleType(models.Model):
    _name = "vehicle.type"
    _description = 'Vehicle Type'

    name = fields.Char()

class VehicleBrand(models.Model):
    _name = "vehicle.brand"
    _description = 'Vehicle Brand'

    name = fields.Char()

class VehiclePowerMode(models.Model):
    _name = "vehicle.power.mode"
    _description = 'Vehicle Power Mode'

    name = fields.Char()

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    accounting_document = fields.Boolean(default=False)
