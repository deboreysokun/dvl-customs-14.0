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


class TaxCalculationLineMakeOperationShipment(models.TransientModel):
    _name = "tax.calculation.line.make.operation.shipment"
    _description = "Tax Calculation to Shipment Operation"

    operation_type = fields.Selection(selection =[
            ('import', 'Import'),
            ('export', 'Export'),
            ('transit', 'Transit')],
            string='Operation Type',)
    transportation_mode = fields.Selection(selection =[
        ('sea', 'By Sea'),
        ('air', 'By Air'),
        ('road', 'By Road'),
        ('other', 'Others')],
        string='Transportation', default='sea')

    @api.model
    def prepare_lines(self, name, kh_name, hs_code, qty, uom ,price_unit, fta_rate, cd, st, vat,
        tax_amount, tax_amount_co, new_tax_rate, remark_hs_code, number):
        return {
            'description': name,
            'description_khmer': kh_name,
            'hs_code_id': hs_code.id,
            'qty': qty,
            'uom_id': uom.id,
            'price_unit': price_unit,
            'fta': fta_rate,
            'cd': hs_code.cd,
            'st': hs_code.st,
            'vat':hs_code.vat,
            'tax_amount': tax_amount,
            'tax_amount_co': tax_amount_co,
            'new_tax_rate' : new_tax_rate,
            'remark_hs_code' : remark_hs_code,
            'number' : number,
        }

    @api.model
    def compute_tax_calculation_line(self, record, lines):
        res = {}
        res['operation_type'] = self.operation_type
        res['transportation_mode'] = self.transportation_mode
        for line in record.line_ids:
            lines.append((0, 0, self.prepare_lines
                (line.name, line.kh_name, line.hs_code_id,
                line.qty, line.uom_id, line.price_unit,
                line.fta_rate, line.hs_code_id.cd, line.hs_code_id.st, line.hs_code_id.vat,
                line.tax_amount, line.tax_amount_co, line.new_tax_rate, line.remark_hs_code, line.number)))
        res['lines'] = lines
        return res

    def make_operation_shipment(self):
        record_names = []
        lines = []
        active_model = self._context.get('active_model')
        records = self.env[active_model].browse(
            self._context.get('active_ids'))
        for record in records:
            record_names.append(record.name)
            res = self.compute_tax_calculation_line(record, lines)

        shipment_id = self.env['operation.shipment'].create({
            'tax_calculation_id': records.id ,
            'operation_type': res['operation_type'],
            'transportation_mode': res['transportation_mode'],
            'line_ids': res['lines'],
        })
        message = _(
            '<strong>Shipment of:</strong> %s </br>') % (
            ', '.join(record_names))
        shipment_id.message_post(body=message)
        return {
            'name': _('Shipment'),
            'view_mode': 'form',
            'target': 'current',
            'res_model': 'operation.shipment',
            'res_id': shipment_id.id,
            'view_id': self.env.ref('devel_logistic_management.view_shipment_operation_form').id,
            'context': "{'operation_type': 'self.operation_type'}",
            'type': 'ir.actions.act_window',
        }
