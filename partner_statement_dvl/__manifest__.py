# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Partner Statement Extension for DVL',
    'version': '14.0.1.4.0',
    'category': 'Accounting & Finance',
    'summary': 'Added New Partner Outstanding Statement For Logistic',
    'author': "A2A Digital",
    'website': 'https://a2a-digital.com/',
    'license': 'AGPL-3',
    'depends': [
        'partner_statement',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/outstanding_statement.xml',
        'views/outstanding_statement_logistic.xml',
        'wizard/statement_logistic_wizard.xml',
    ],
    'installable': True,
    'application': False,
}
