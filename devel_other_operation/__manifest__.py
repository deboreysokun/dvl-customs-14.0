# -*- coding: utf-8 -*-
#############################################################################
#
#    Devel Logistics Co. Ltd - Other Operation App
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
    'name': 'Devel Other Operation (DVL)',
    'version': '14.0.1.2.0',
    'summary': """ Manage Other Service Operations of Devel Logistics .Co ,Ltd""",
    'sequence': 10,
    'description': """
                    """,
    'license': 'OPL-1',
    'author': 'A2A Digital',
    'website': "https://a2a-digital.com",
    'company': 'A2A Digital',
    'maintainer': 'A2A Digital',
    'depends': ['devel_logistic_management'],
    'data': [
        'security/dvl_other_security.xml',
        'security/ir.model.access.csv',
        'wizard/create_sales_quotation_view.xml',
        'wizard/other_operation_resequence_view.xml',
        'wizard/res_partner_aging_customer.xml',
        'wizard/other_operation_expense_line_view.xml',
        'views/account_move_view.xml',
        'views/sale_quotation_view.xml',
        'views/other_operation_view.xml',
        'reports/report_sale_normal_quotation.xml',
        'reports/report_credit_note_other_service.xml',
        'reports/report_debit_note_other_service.xml',
        'reports/report_summary_other_service.xml',
    ],
    'qweb': [

    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
