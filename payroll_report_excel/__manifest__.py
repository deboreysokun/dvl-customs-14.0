{
    'name': 'payroll report in excel',
    'version': '14.0.1.0.0',
    'category': 'payroll',
    'sequence': 60,
    'summary': 'shows the payroll report in xlsx format',
    'description': "It shows payroll report in excel for given month",
    'author':'aswathy, A2A Digital',
    'depends': ['base','hr', 'hr_payroll_community'],
    'data': [
      'security/ir.model.access.csv',
      'wizard/payroll_report_wiz.xml',
      ],
    'installable': True,
    'auto_install': False,
    'application': False,
}