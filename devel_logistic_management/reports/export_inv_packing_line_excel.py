# -*- coding: utf-8 -*-

from datetime import time

from odoo import models, api, _
from odoo.exceptions import UserError

class InvPackingLineXls(models.AbstractModel):
    _name = 'report.devel_logistic_management.inv_packing_lines.xlsx'
    _inherit = ['report.report_xlsx.abstract']

    def generate_xlsx_report(self, workbook, data, lines):
        sheet = workbook.add_worksheet()
        format11 = workbook.add_format({
            'font_size': 12, 'align': 'center', 'bold': True,
            'border': True, 'bg_color': '#d0cece'})
        format12 = workbook.add_format({'font_size': 12,'align': 'right'})
        sheet.set_column(1, 3, 15)
        sheet.set_column(4, 5, 40)
        sheet.set_column(6, 9, 10)
        sheet.set_column(10, 28, 20)

        model = self.env.context.get('active_model')
        shipment = self.env[model].browse(
            self.env.context.get('active_ids', []))

        inv_pakcing_lines = shipment.line_ids

        sheet.write(0,0, "ITEM_Nbr", format11)
        sheet.write(0,1, "HSCODE", format11)
        sheet.write(0,2, "HSCODEonFTA", format11)
        sheet.write(0,3, "ItemCOcode", format11)
        sheet.write(0,4, "ITEM_DESCRIPTION", format11)
        sheet.write(0,5, "ITEM_DESCRIPTION_KH", format11)
        sheet.write(0,6, "ITEM_UNIT", format11)
        sheet.write(0,7, "ITEM_QTY", format11)
        sheet.write(0,8, "ITEM_NW", format11)
        sheet.write(0,9, "ITEM_GW", format11)
        sheet.write(0,10, "ITEM_UNIT_PRICE", format11)
        sheet.write(0,11, "ItemAdditionalFeeText", format11)
        sheet.write(0,12, "ItemAdditionalFee", format11)
        sheet.write(0,13, "FTA_CD", format11)
        sheet.write(0,14, "NbrInCo", format11)
        sheet.write(0,15, "CoCriteria", format11)
        sheet.write(0,16, "ITEM_FOB", format11)
        sheet.write(0,17, "VType", format11)
        sheet.write(0,18, "VLeftHandDrive", format11)
        sheet.write(0,19, "VPowerMode", format11)
        sheet.write(0,20, "NEW_USED", format11)
        sheet.write(0,21, "ITEM_BRAND", format11)
        sheet.write(0,22, "ITEM_MODEL", format11)
        sheet.write(0,23, "ITEM_MODELYEAR", format11)
        sheet.write(0,24, "ITEM_CAPACITY", format11)
        sheet.write(0,25, "ITEM_VIN", format11)
        sheet.write(0,26, "ITEM_ENG", format11)
        sheet.write(0,27, "VGvW", format11)
        sheet.write(0,28, "VOtherInfo", format11)
        sheet.write(0,29, "IMEI1", format11)
        sheet.write(0,30, "IMEI2", format11)
        sheet.write(0,31, "IMEI3", format11)
        sheet.write(0,32, "NBR_PACKAGE", format11)
        sheet.write(0,33, "PACKAGE_TYPE", format11)
        sheet.write(0,34, "SUPP_CODE", format11)
        sheet.write(0,35, "SUPP_QTY", format11)
        row=1
        line_index = 1
        description = v_capacity = " "

        for line in inv_pakcing_lines:
            if line.description:
                description = str(line.description)
            if line.item_manufacturing_date:
                description += ',MFG: ' + str(line.item_manufacturing_date)
            if line.item_expiry_date:
                description += ',EXP: ' + str(line.item_expiry_date)

            sheet.write_number(row,0, line_index, format12)
            sheet.write(row,1, str(line.hs_code_id.tariff_code) or '',)
            sheet.write(row,2, line.remark_hs_code or '',) #HSCODEonFTA
            sheet.write(row,3, line.origin_country_id.code or '',)
            sheet.write(row,4, description or '',)
            sheet.write(row,5, line.description_khmer or '',)
            sheet.write(row,6, str(line.uom_id.name) or '',)
            sheet.write_number(row,7, line.qty, format12)
            sheet.write_number(row,8, line.net_weight, format12)
            sheet.write_number(row,9, line.gross_weight, format12)
            sheet.write_number(row,10,line.price_unit, format12)
            if shipment.co_form_id:
                sheet.write(row,13, int(line.fta), format12)
                sheet.write(row,14, _(line.number_in_co) if line.number_in_co != 0 else _(''), format12)
                sheet.write(row,15, line.co_criteria or '', format12)
                sheet.write(row,16, _(int(str(line.price_subtotal_fob))) if line.price_subtotal_fob != 0 else _(''), format12)

            if shipment.is_vehicle or shipment.mix_commodity:
                if line.v_type:
                    sheet.write(row,17, line.v_type.name or '',)
                    sheet.write(row,18, _('LEFT-HAND-DRIVE') if line.v_left_hand_drive == 'left' else (_('RIGHT-HAND-DRIVE') if line.v_left_hand_drive == 'right' else _('')),)
                    sheet.write(row,19, line.v_power_mode.name or '',)
                    sheet.write(row,20, _('NEW') if line.new_used == 'new' else (_('USED') if line.new_used == 'used' else _('')),)
                    sheet.write(row,21, line.v_brand.name or '',)
                    sheet.write(row,22, line.v_model or '',)
                    sheet.write(row,23, int(str(line.v_model_year)) or '',format12)
                    sheet.write(row,24, _(float(str(line.v_capacity))) if line.v_capacity else _(''),format12)
                    sheet.write(row,25, line.v_vin or '',)
                    sheet.write(row,26, line.v_eng or '',)
                    sheet.write(row,27, line.v_gvw or '',)
                    sheet.write(row,28, line.v_other_info or '',)

            sheet.write(row,32, line.nbr_packages or '',format12)
            sheet.write(row,33, line.package_type or '',format12)
            sheet.write(row,34, line.supplementary_unicode or '',format12)
            sheet.write(row,35, line.supplementary_qty or '',format12)
            row +=1
            line_index +=1
            description = " "
