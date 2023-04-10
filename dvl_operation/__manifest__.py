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
    'name': 'DVL Operation',
    'version': '14.0.1.2.0',
    'summary': """ Inherit operation shipment""",
    'sequence': 10,
    'description': """
                    """,
    'license': 'OPL-1',
    'author': 'A2A Digital',
    'website': "https://a2a-digital.com",
    'company': 'A2A Digital',
    'maintainer': 'A2A Digital',
    'depends': ['devel_logistic_management'],
    'data': [],
        
    'qweb': [
            'views/account_move.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
