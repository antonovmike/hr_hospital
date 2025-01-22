# -*- coding: utf-8 -*-
{
    'name': "Hospital",

    'summary': "",

    'author': "Antonov Mike",
    'website': "https://github.com/antonovmike",

    'category': 'Human Resources',
    'license': 'OPL-1',
    'version': '17.0.0.0.0',

    'depends': ['base', 'web'],

    'external_dependencies': {'python': [], },

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/physician.xml',
        'views/patient.xml',
        'views/disease.xml',
        'views/diagnosis.xml',
        'views/patient_visits.xml',
        'views/physician_change_history.xml',
        'views/physician_schedule.xml',
        'wizard/mass_reassign_physician_wizard_view.xml',
        'wizard/physician_disease_report_wizard_view.xml',
        'reports/physician_disease_report.xml',
        # 'views/templates.xml',
        # 'demo/demo.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],

    'installable': True,
    'auto_install': False,

    'price': 0,
    'currency': 'EUR',
}
