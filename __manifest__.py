# -*- coding: utf-8 -*-
{
    'name': "Hospital",

    'summary': "",

    'author': "Antonov Mike",
    'website': "https://github.com/antonovmike",

    'category': 'Human Resources',
    'license': 'OPL-1',
    'version': '17.0.0.0.0',

    'depends': ['base', 'web', 'mail'],

    'external_dependencies': {'python': [], },

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'wizard/mass_reassign_physician_wizard_view.xml',
        'wizard/physician_disease_report_wizard_view.xml',
        'wizard/reschedule_appointment_wizard_views.xml',
        'wizard/generate_schedule_wizard_views.xml',
        'views/menu.xml',
        'views/physician.xml',
        'views/patient.xml',
        'views/patient_visits.xml',
        'views/diagnosis.xml',
        'views/disease.xml',
        'views/physician_change_history.xml',
        'views/physician_schedule.xml',
        'reports/physician_disease_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],

    'installable': True,
    'auto_install': False,

    'price': 0,
    'currency': 'EUR',
}
