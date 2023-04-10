# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import io
import xlrd
import babel
import logging
import tempfile
import binascii
from io import StringIO
from datetime import date, datetime, time, timedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import Warning, UserError, ValidationError

_logger = logging.getLogger(__name__)

try:
    import csv
except ImportError:
    _logger.debug('Cannot `import csv`.')
try:
    import xlwt
except ImportError:
    _logger.debug('Cannot `import xlwt`.')
try:
    import cStringIO
except ImportError:
    _logger.debug('Cannot `import cStringIO`.')
try:
    import base64
except ImportError:
    _logger.debug('Cannot `import base64`.')


class ImportInvAndPackingList(models.TransientModel):
    _name = 'import.inv.packing.list'
    _description = 'Import Operation Inv and PL'

    file = fields.Binary(string="Upload File")

    def import_inv_pl(self):
        if not self.file:
            raise ValidationError(_("Please Upload File to Import Inv and Packing List!"))

        shipment_id = self.env['operation.shipment'].browse(
        self._context.get('active_ids'))

        #unlink all existing lines in INV and PL of shipment to avoid create new line
        if shipment_id.line_ids:
            shipment_id.line_ids = [(5, 0, 0)]

        try:
            file = tempfile.NamedTemporaryFile(delete= False,suffix=".xlsx")
            file.write(binascii.a2b_base64(self.file))
            file.seek(0)
            values = {}
            workbook = xlrd.open_workbook(file.name)
            sheet = workbook.sheet_by_index(0)
        except Exception:
            raise ValidationError(_("Please Select Valid File Format !"))

        for row_no in range(sheet.nrows):
            val = {}
            if row_no <= 0:
                fields = list(map(lambda row:row.value.encode('utf-8'), sheet.row(row_no)))
            else:
                line = list(map(lambda row:isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value), sheet.row(row_no)))
                values.update( {
                    'hs_code_id': line[1],
                    'remark_hs_code': line[2],
                    'origin_country_id':line[3],
                    'description':line[4],
                    'description_khmer':line[5],
                    'qty':line[6],
                    'uom_id':line[7],
                    'packing_list_qty':line[8],
                    'packing_list_uom_id':line[9],
                    'number_in_book':line[10],
                    'price_unit':line[11],
                    'net_weight':line[12],
                    'gross_weight':line[13],
                    'manuf_date' : line[14],
                    'expiry_date' : line[15],
                    'fta': line[16],
                    'number_in_co':line[17],
                    'fob_amount':line[18],
                    'co_criteria':line[19],
                    'new_tax_rate': line[20],
                    'wheel_type': line[21],
                    'v_type':line[22],
                    'v_left_hand_drive':line[23],
                    'v_power_mode':line[24],
                    'new_used':line[25],
                    'v_brand':line[26],
                    'v_model':line[27],
                    'v_model_year':line[28],
                    'v_capacity':line[29],
                    'v_vin':line[30],
                    'v_eng':line[31],
                    'v_gvw':line[32],
                    'v_other_info':line[33],
                    })
                res = self.create_inv_pl(values)

    def create_inv_pl(self, values):
        shipment_id = self.env['operation.shipment'].browse(
            self._context.get('active_ids'))

        inv_pl_line = self.env['operation.shipment.item']
        hs_code_id = self.get_hscode(values.get('hs_code_id'))
        origin_country_id = self.get_origin_country(values.get('origin_country_id'))
        uom_id = self.get_uom(values.get('uom_id'))
        packing_list_uom_id = self.get_packing_list_uom(values.get('packing_list_uom_id'))

        manuf_date = self.get_manuf_date(values.get('manuf_date'))
        expiry_date = self.get_expiry_date(values.get('expiry_date'))

        v_type_id = self.get_vtype(values.get('v_type'))
        v_power_mode_id = self.get_v_power_mode(values.get('v_power_mode'))
        v_brand_id = self.get_v_brand(values.get('v_brand'))

        new_used = v_left_hand_drive = wheel_type = number_in_book = number_in_co = ''
        v_model_year = v_capacity = ''

        if values.get('new_used') == 'NEW':
            new_used = 'new'
        elif values.get('new_used') == 'new':
            new_used = 'new'
        elif values.get('new_used') == 'New':
            new_used = 'new'
        elif values.get('new_used') == 'USED':
            genew_usednder = 'used'
        elif values.get('new_used') == 'used':
            new_used = 'used'
        elif values.get('new_used') == 'Used':
            new_used = 'used'
        else:
            new_used = ''

        if values.get('v_left_hand_drive') == 'LEFT-HAND-DRIVE':
            v_left_hand_drive ='left'
        elif values.get('v_left_hand_drive') == 'left':
            v_left_hand_drive ='left'
        elif values.get('v_left_hand_drive') == 'right':
            v_left_hand_drive ='right'
        elif values.get('v_left_hand_drive') == 'RIGHT-HAND-DRIVE':
            v_left_hand_drive = 'right'
        else:
            v_left_hand_drive = ''

        if values.get('wheel_type') == '4WD':
            wheel_type = '4wd'
        elif values.get('wheel_type') == '2WD':
            wheel_type = '2wd'
        else:
            wheel_type = ''

        if not values.get('number_in_book'):
            number_in_book = ' '
        else:
            number_in_book = int(float(str(values.get('number_in_book'))))

        if not values.get('number_in_co'):
            number_in_co = ' '
        else:
            number_in_co = int(float(str(values.get('number_in_co'))))

        if not values.get('v_model_year'):
            v_model_year = ' '
        else:
            v_model_year = int(float(str(values.get('v_model_year'))))

        if not values.get('v_capacity'):
            v_capacity = ' '
        else:
            v_capacity = str(values.get('v_capacity'))

        vals = {
                'shipment_id': shipment_id.id,
                'hs_code_id': hs_code_id.id,
                'remark_hs_code': values.get('remark_hs_code'),
                'origin_country_id': origin_country_id.id ,
                'description': values.get('description'),
                'description_khmer': values.get('description_khmer'),
                'qty': values.get('qty'),
                'uom_id': uom_id.id,
                'packing_list_qty': values.get('packing_list_qty'),
                'packing_list_uom_id': packing_list_uom_id.id,
                'number': number_in_book,
                'price_unit': values.get('price_unit'),
                'net_weight': values.get('net_weight'),
                'gross_weight': values.get('gross_weight'),
                'item_manufacturing_date' : manuf_date,
                'item_expiry_date' : expiry_date,
                'fta': values.get('fta'),
                'number_in_co': number_in_co,
                'price_subtotal_fob': values.get('fob_amount'),
                'co_criteria':values.get('co_criteria'),
                'new_tax_rate': values.get('new_tax_rate'),
                'wheel_type': wheel_type,
                'v_type': v_type_id.id,
                'v_left_hand_drive': v_left_hand_drive,
                'v_power_mode': v_power_mode_id.id,
                'new_used': new_used,
                'v_brand': v_brand_id.id,
                'v_model': values.get('v_model'),
                'v_model_year': v_model_year,
                'v_capacity': v_capacity,
                'v_vin': values.get('v_vin'),
                'v_eng': values.get('v_eng'),
                'v_gvw': values.get('v_gvw'),
                'v_other_info': values.get('v_other_info'),
                }

        res = inv_pl_line.create(vals)
        return res

    def get_hscode(self, name):
        hscode = self.env['hs.code'].search([('tariff_code', '=', name)],limit=1)
        if hscode or not hscode:
            return hscode
        else:
            raise UserError(_('"%s" HSCODE is not found in system !') % name)

    def get_origin_country(self, name):
        country = self.env['res.country'].search([('code', '=', name)],limit=1)
        if country or not country:
            return country
        else:
            raise UserError(_('"%s" Country is not found in system !') % name)

    def get_uom(self, name):
        uom = self.env['uom.unit'].search([('name', '=', name)],limit=1)
        if uom or not uom:
            return uom
        else:
            raise UserError(_('"%s" UOM is not found in system !') % name)

    def get_packing_list_uom(self, name):
        pl_uom = self.env['uom.unit'].search([('name', '=', name)],limit=1)
        if pl_uom or not pl_uom:
            return pl_uom
        else:
            raise UserError(_('"%s" PL UOM is not found in system !') % name)

    def get_vtype(self, name):
        v_type = self.env['vehicle.type'].search([('name', '=', name)],limit=1)
        if v_type or not v_type:
            return v_type
        else:
            raise UserError(_('"%s" Vehicle Type is not found in system !') % name)

    def get_v_power_mode(self, name):
        v_power_mode = self.env['vehicle.power.mode'].search([('name', '=', name)],limit=1)
        if v_power_mode or not v_power_mode:
            return v_power_mode
        else:
            raise UserError(_('"%s" Vehicle Power Mode is not found in system !') % name)

    def get_v_brand(self, name):
        v_brand = self.env['vehicle.brand'].search([('name', '=', name)],limit=1)
        if v_brand or not v_brand:
            return v_brand
        else:
            raise UserError(_('"%s" Vehicle Brand is not found in system !') % name)

    def get_expiry_date(self, date):
        try:
            if date:
                py_date = datetime(*xlrd.xldate_as_tuple(float(date), 0))
                expiry_date = datetime.strptime(str(py_date), '%Y-%m-%d %H:%M:%S')
                return expiry_date
            else:
                pass
        except Exception:
            _logger.info("Wrong Expiry Date Format %s" % (date), exc_info=True)
            raise ValidationError(_('Wrong Expiry Date Format ! Date Should be in format YYYY-MM-DD'))

    def get_manuf_date(self, date):
        try:
            if date:
                py_date = datetime(*xlrd.xldate_as_tuple(float(date), 0))
                manuf_date = datetime.strptime(str(py_date), '%Y-%m-%d %H:%M:%S')
                return manuf_date
            else:
                pass
        except Exception:
            _logger.info("Wrong Manufacturing Date Format %s" % (date), exc_info=True)
            raise ValidationError(_('Wrong Manufacturing Date Format ! Date Should be in format YYYY-MM-DD'))
