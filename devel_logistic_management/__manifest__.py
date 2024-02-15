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

{
    'name': 'Devel Logistics Operation (DVL)',
    'version': '14.0.5.84.38',
    'summary': """ Manage Operations of Devel Logistics .Co ,Ltd""",
    'sequence': 10,
    'description': """
                    Import Operation, Export Opertion, Trasit Operation,
                    HS Code For customs in Cambodia

                    """,
    'license': 'OPL-1',
    'author': 'A2A Digital',
    'website': "https://a2a-digital.com",
    'company': 'A2A Digital',
    'maintainer': 'A2A Digital',
    'depends': ['base', 'base_import', 'account', 'hr','mail', 'contacts', 'report_xlsx',
        'mail_preview_base'
        ],
    'data': [
        'security/dvl_security.xml',
        'security/ir.model.access.csv',
        'views/web.xml',
        'views/dvl_menu.xml',
        'views/configuration_view.xml',
        'data/data_account_type.xml',
        'data/uom_unit.xml',
        'data/shipment_type.xml',
        'data/ir_sequence.xml',
        'data/co_form_data.xml',
        'data/container_type.xml',
        'data/eandf_consignment.xml',
        'data/mail_data.xml',
        'data/province_list.xml',
        'data/report_paperformat_data.xml',
        'wizard/tax_calculation_to_shipment_view.xml',
        'wizard/container_deposit_view.xml',
        'wizard/expense_lines_payment_view.xml',
        'wizard/expense_lines_reimbursement_view.xml',
        'wizard/res_partner_aging_customer.xml',
        'wizard/res_partner_aging_supplier.xml',
        'wizard/add_to_expense_line_view.xml',
        'wizard/operation_shipment_review_done.xml',
        'wizard/create_quotation_template_view.xml',
        'wizard/import_inv_and_packinglist_view.xml',
        'wizard/res_partner_invoice_payment_view.xml',
        'wizard/cash_advance_payment_view.xml',
        'wizard/print_expense_summary.xml',

        'views/tax_calculation_view.xml',
        'views/shipment_expense_lines_view.xml',
        'views/operation_shipment.xml',
        'views/operation_status_view.xml',
        'reports/document_report.xml',
        'reports/report_co_form.xml',
        'reports/report_co_attachment_doc.xml',
        'reports/report_inv_packing_list.xml',
        'reports/report_authorization_trader.xml',
        'reports/report_form_apply_permit.xml',
        'reports/report_permit_doc.xml',
        'reports/report_permit_export_doc.xml',
        'views/res_partner_views.xml',
        'views/truck_booking_view.xml',
        'reports/report_booking_order_doc.xml',
        'reports/report_expense_summary.xml',
        'reports/report_export_inv_packing_list.xml',
        'reports/report_export_requirement_letter.xml',
        'reports/report_gurantee_letter.xml',
        'reports/report_vgm.xml',
        'reports/report_draft_bl.xml',
        'reports/report_inspection_letter.xml',
        'reports/report_export_container_list.xml',
        'views/hr_employee.xml',
        'views/storage_demurrage_view.xml',
        'views/account_move_configuration.xml',
        'views/account_move_view.xml',
        'reports/report_cover_file_shipment.xml',
        'reports/report_cash_payment_request_shipment.xml',
        'reports/report_closing_file_shipment.xml',
        'reports/report_tax_invoice.xml',
        'reports/report_debit_note_invoice.xml',
        'reports/report_reimbursement_receipt.xml',
        'views/sale_quotation_view.xml',
        'views/sale_quotation_template_view.xml',
        'reports/report_sale_quotation.xml',
        'reports/report_transit_inv_packing_list.xml',
        'reports/report_authorization_broker.xml',
        'reports/report_transit_truck_bill.xml',
        'reports/report_preview_document.xml',
        'reports/report_credit_note_invoice.xml',
        'reports/report_normal_invoice.xml',
        'reports/report_partner_invoice_payment.xml',
        'reports/report_shipment_template.xml',
        'views/shipment_template.xml',
        'reports/report_partner_shipment_invoice_status.xml',
        'reports/report_normal_invoice__dvl.xml',
        'reports/report_law_invoice.xml',
    ],
    'qweb': [
        'static/src/xml/one2many_selection.xml',
        'static/src/xml/res_partner_show_bank_info.xml',
        'static/src/xml/account_upload_attachment.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
