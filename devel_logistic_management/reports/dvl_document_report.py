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

import time, json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ReportCoForm(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_co_form'
    _description = 'CO Form Document'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['operation.shipment'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'operation.shipment',
            'docs': docs,
            'khmerformattedDate': self.env['operation.shipment'].khmer_date_format()
        }


class ReportInvPackingList(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_inv_packing_list'
    _description = 'Invoice and Packing List'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['operation.shipment'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'operation.shipment',
            'docs': docs,
        }

class ReportAuthorizationForm(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_authorization_trader'
    _description = 'Authorization Form Document'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['operation.shipment'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'operation.shipment',
            'docs': docs,
            'khmerformattedDate': self.env['operation.shipment'].khmer_date_format()
        }

class ReportImportPermit(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_import_permit_doc'
    _description = 'Import Permit Document'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['operation.shipment'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'operation.shipment',
            'docs': docs,
            'khmerformattedDate': self.env['operation.shipment'].khmer_date_format()
        }

class ReportExportPermit(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_export_permit_doc'
    _description = 'Export Permit Document'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['operation.shipment'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'operation.shipment',
            'docs': docs,
            'khmerformattedDate': self.env['operation.shipment'].khmer_date_format()
        }

class ReportExportRequirementLetter(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_export_req_letter'
    _description = 'Export Requirement Letter'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['operation.shipment'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'operation.shipment',
            'docs': docs,
            'khmerformattedDate': self.env['operation.shipment'].khmer_date_format()
        }

class ReportGuaranteeLetter(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_guarantee_letter'
    _description = 'Export Guarantee Letter'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['operation.shipment'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'operation.shipment',
            'docs': docs,
            'khmerformattedDate': self.env['operation.shipment'].khmer_date_format()
        }

class ReportTransitAuthorizationForm(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_authorization_broker'
    _description = 'Transit Authorization Form Document'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['operation.shipment'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'operation.shipment',
            'docs': docs,
            'khmerformattedDate': self.env['operation.shipment'].khmer_date_format()
        }

class ReportContainerListForm(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_export_container_list'
    _description = 'List of Container'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['operation.shipment'].browse(docids)
        shipment = self.env['operation.shipment']
        firstdate, lastdate = shipment.get_date_range_from_Week()

        return {
            'doc_ids': docids,
            'doc_model': 'operation.shipment',
            'docs': docs,
            'firstdate': firstdate,
            'lastdate': lastdate,
        }

class ReportPartnerInvoicePayment(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_partner_invoice_payment'
    _description = 'Partner Invoice Payment History'

    def _get_invoice_data(self, company_id, start_date, end_date, ids):
        invoices = self.env['account.move'].search([
            ('company_id', 'child_of', company_id),
            ('partner_id', 'in', ids),
            ('invoice_date', '>=', start_date), ('invoice_date', '<=', end_date),
            ('state', 'not in', ('draft', 'cancel')),
            ('move_type', '=', 'out_invoice'),
            ])
        return invoices.sorted(lambda x: x.invoice_date)

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        invoice_data = self._get_invoice_data(data['company_id'], data['start_date'], data['end_date'], data['partner_ids'])
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'get_data': invoice_data,
        }

class ReportPartnerShipmentInvoice(models.AbstractModel):
    _name = 'report.devel_logistic_management.report_partner_shp_inv_status'
    _description = 'Partner Shipment Invoice Status'

    def _get_shipment_with_invoiced(self, company_id,  start_date, end_date, ids):
        shipments = self.env['operation.shipment'].search([
            ('company_id', 'child_of', company_id),
            ('customer_id', 'in', ids),
            ('date', '>=', start_date), ('date', '<=', end_date),
            ]).filtered(lambda x: x.issued_invoice_date != False)
        return shipments.sorted(lambda x: x.date)

    def _get_shipment_no_issued_invoice(self, company_id, start_date, end_date, ids):
        shipments = self.env['operation.shipment'].search([
            ('company_id', 'child_of', company_id),
            ('customer_id', 'in', ids),
            ('date', '>=', start_date), ('date', '<=', end_date),
        ]).filtered(lambda x: x.issued_invoice_date == False)
        return shipments.sorted(lambda x: x.date)

    @api.model
    def _get_report_values(self, docids, data=None):
        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_id'))
        shipment_with_invoice = self._get_shipment_with_invoiced(data['company_id'], data['start_date'], data['end_date'], data['partner_ids'])
        shipment_without_invoice = self._get_shipment_no_issued_invoice(data['company_id'], data['start_date'], data['end_date'], data['partner_ids'])
        return {
            'doc_ids': self.ids,
            'doc_model': model,
            'data': data,
            'docs': docs,
            'shipment_with_invoice': shipment_with_invoice,
            'shipment_without_invoice': shipment_without_invoice,
        }
