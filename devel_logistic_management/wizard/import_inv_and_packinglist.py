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

        # unlink all existing lines in INV and PL of shipment to avoid create new line
        if shipment_id.line_ids:
            shipment_id.line_ids = [(5, 0, 0)]

        try:
            file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
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
                fields = list(map(lambda row: row.value.encode('utf-8'), sheet.row(row_no)))
            else:
                line = list(
                    map(lambda row: isinstance(row.value, bytes) and row.value.encode('utf-8') or str(row.value),
                        sheet.row(row_no)))

                # Handle description parsing (may contain manufacturing and expiry dates)
                description = line[5]
                manuf_date = None
                expiry_date = None

                # Extract dates from description if present
                if 'MFG:' in description:
                    parts = description.split('MFG:')
                    description = parts[0].strip()
                    date_part = parts[1].strip()
                    if ',' in date_part:
                        manuf_date = date_part.split(',')[0].strip()

                if 'EXP:' in description:
                    parts = description.split('EXP:')
                    if 'MFG:' not in description:
                        description = parts[0].strip()
                    expiry_date = parts[1].strip().split(',')[0] if ',' in parts[1] else parts[1].strip()

                values.update({
                    'hs_code_id': line[1],  # HSCODE
                    'remark_hs_code': line[2],  # HSCODEonFTA
                    'co_form': line[3],  # CO_FORM
                    'origin_country_id': line[4],  # ItemCOcode
                    'description': description,  # ITEM_DESCRIPTION
                    'description_khmer': line[6],  # ITEM_DESCRIPTION_KH
                    'uom_id': line[7],  # ITEM_UNIT
                    'qty': line[8],  # ITEM_QTY
                    'net_weight': line[9],  # ITEM_NW
                    'gross_weight': line[10],  # ITEM_GW
                    'price_unit': line[11],  # ITEM_UNIT_PRICE
                    'nbr_packages': line[12],  # Nbr_Package
                    'package_type': line[13],  # Pacakge_Code
                    'supplementary_qty': line[14],  # Supplementary_Unit_Qty
                    'item_additional_fee_text': line[15],  # ItemAdditionalFeeText
                    'item_additional_fee': line[16],  # ItemAdditionalFee
                    'fta': line[17],  # FTA_CD
                    'number_in_co': line[18],  # NbrInCo
                    'co_criteria': line[19],  # CoCriteria
                    'fob_amount': line[20],  # ITEM_FOB
                    'v_type': line[21],  # VType
                    'v_left_hand_drive': line[22],  # VLeftHandDrive
                    'v_power_mode': line[23],  # VPowerMode
                    'new_used': line[24],  # NEW_USED
                    'v_brand_typing': line[25],  # ITEM_BRAND
                    'v_model': line[26],  # ITEM_MODEL
                    'v_model_year': line[27],  # ITEM_MODELYEAR
                    'v_capacity': line[28],  # ITEM_CAPACITY
                    'v_power_unit_code': line[29],  # VPowerUnitCode
                    'v_color': line[30],  # VColor
                    'v_vin': line[31],  # ITEM_VIN
                    'v_eng': line[32],  # ITEM_ENG
                    'v_gvw': line[33],  # VGvW
                    'v_other_info': line[34],  # VOtherInfo
                    'imei1': line[35],  # IMEI1
                    'imei2': line[36],  # IMEI2
                    'imei3': line[37],  # IMEI3
                    'item_manufacturing_date': manuf_date,  # Extracted from description
                    'item_expiry_date': expiry_date,  # Extracted from description
                })
                res = self.create_inv_pl(values)

    def create_inv_pl(self, values):
        shipment_id = self.env['operation.shipment'].browse(
            self._context.get('active_ids'))

        inv_pl_line = self.env['operation.shipment.item']
        hs_code_id = self.get_hscode(values.get('hs_code_id'))
        origin_country_id = self.get_origin_country(values.get('origin_country_id'))
        uom_id = self.get_uom(values.get('uom_id'))

        # Parse the dates if they're provided as strings
        manuf_date = self.parse_date(values.get('item_manufacturing_date')) if values.get(
            'item_manufacturing_date') else None
        expiry_date = self.parse_date(values.get('item_expiry_date')) if values.get('item_expiry_date') else None

        v_type_id = self.get_vtype(values.get('v_type'))
        v_power_mode_id = self.get_v_power_mode(values.get('v_power_mode'))
        v_brand_typing_id = self.get_v_brand_typing(values.get('v_brand_typing'))

        # Handle left-hand drive
        v_left_hand_drive = ''
        if values.get('v_left_hand_drive') == 'LEFT-HAND-DRIVE':
            v_left_hand_drive = 'left'
        elif values.get('v_left_hand_drive') == 'RIGHT-HAND-DRIVE':
            v_left_hand_drive = 'right'

        # Handle new/used
        new_used = ''
        if values.get('new_used') == 'NEW':
            new_used = 'new'
        elif values.get('new_used') == 'USED':
            new_used = 'used'

        # Handle numeric fields safely
        number_in_co = ''
        if values.get('number_in_co') and values.get('number_in_co') != '':
            try:
                number_in_co = int(float(str(values.get('number_in_co'))))
            except:
                number_in_co = ''

        v_model_year = ''
        if values.get('v_model_year') and values.get('v_model_year') != '':
            try:
                v_model_year = int(float(str(values.get('v_model_year'))))
            except:
                v_model_year = ''

        v_capacity = values.get('v_capacity', '')

        vals = {
            'shipment_id': shipment_id.id,
            'hs_code_id': hs_code_id.id if hs_code_id else False,
            'remark_hs_code': values.get('remark_hs_code'),
            'origin_country_id': origin_country_id.id if origin_country_id else False,
            'description': values.get('description'),
            'description_khmer': values.get('description_khmer'),
            'qty': values.get('qty'),
            'uom_id': uom_id.id if uom_id else False,
            'price_unit': values.get('price_unit'),
            'net_weight': values.get('net_weight'),
            'gross_weight': values.get('gross_weight'),
            'item_manufacturing_date': manuf_date,
            'item_expiry_date': expiry_date,
            'fta': values.get('fta'),
            'number_in_co': number_in_co,
            'price_subtotal_fob': values.get('fob_amount'),
            'co_criteria': values.get('co_criteria'),
            'nbr_packages': values.get('nbr_packages'),
            'package_type': values.get('package_type'),
            'supplementary_qty': values.get('supplementary_qty'),
            'v_type': v_type_id.id if v_type_id else False,
            'v_left_hand_drive': v_left_hand_drive,
            'v_power_mode': v_power_mode_id.id if v_power_mode_id else False,
            'new_used': new_used,
            'v_brand_typing': values.get('v_brand_typing', False),
            'v_model': values.get('v_model'),
            'v_model_year': v_model_year,
            'v_capacity': v_capacity,
            'v_vin': values.get('v_vin'),
            'v_eng': values.get('v_eng'),
            'v_gvw': values.get('v_gvw'),
            'v_other_info': values.get('v_other_info'),
        }

        # Add new fields if they exist in the model
        additional_fields = [
            'imei1', 'imei2', 'imei3', 'v_power_unit_code', 'v_color',
            'item_additional_fee_text', 'item_additional_fee'
        ]

        for field in additional_fields:
            if hasattr(inv_pl_line, field) and values.get(field):
                vals[field] = values.get(field)

        res = inv_pl_line.create(vals)
        return res

    def get_hscode(self, name):
        if not name or name == '':
            return False
        hscode = self.env['hs.code'].search([('tariff_code', '=', name)], limit=1)
        if hscode:
            return hscode
        else:
            raise UserError(_('"%s" HSCODE is not found in system !') % name)

    def get_origin_country(self, name):
        if not name or name == '':
            return False
        country = self.env['res.country'].search([('code', '=', name)], limit=1)
        if country:
            return country
        else:
            raise UserError(_('"%s" Country is not found in system !') % name)

    def get_uom(self, name):
        if not name or name == '':
            return False
        uom = self.env['uom.unit'].search([('name', '=', name)], limit=1)
        if uom:
            return uom
        else:
            raise UserError(_('"%s" UOM is not found in system !') % name)

    def get_vtype(self, name):
        if not name or name == '':
            return False
        v_type = self.env['vehicle.type'].search([('name', '=', name)], limit=1)
        if v_type:
            return v_type
        else:
            raise UserError(_('"%s" Vehicle Type is not found in system !') % name)

    def get_v_power_mode(self, name):
        if not name or name == '':
            return False
        v_power_mode = self.env['vehicle.power.mode'].search([('name', '=', name)], limit=1)
        if v_power_mode:
            return v_power_mode
        else:
            raise UserError(_('"%s" Vehicle Power Mode is not found in system !') % name)

    def get_v_brand_typing(self, name):
        # Simply return the name as is, or False if empty
        return name if name else False

    def parse_date(self, date_str):
        """Parse date from string format"""
        try:
            if not date_str:
                return None

            # Try to parse as Excel date first
            try:
                py_date = datetime(*xlrd.xldate_as_tuple(float(date_str), 0))
                return py_date
            except:
                pass

            # Try common date formats
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y']:
                try:
                    return datetime.strptime(date_str, fmt)
                except:
                    continue

            return None
        except Exception as e:
            _logger.info("Wrong Date Format %s: %s" % (date_str, e), exc_info=True)
            return None
