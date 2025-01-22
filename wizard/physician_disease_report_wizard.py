from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import models, fields


class PhysicianDiseaseReportWizard(models.TransientModel):
    _name = 'hr.hospital.physician.disease.report.wizard'
    _description = 'Physician Disease Report Wizard'

    physician_ids = fields.Many2many(
        'hr.hospital.physician',
        'physician_disease_report_rel',
        'wizard_id',
        'physician_id',
        string='Physicians',
        required=True
    )
    month = fields.Date(
        required=True,
        default=fields.Date.context_today
    )

    def action_generate_report(self):
        self.ensure_one()

        # Calculate start and end dates for the selected month
        start_date = date(self.month.year, self.month.month, 1)
        end_date = start_date + relativedelta(months=1, days=-1)

        # Get all diagnoses for selected physicians in the given month
        diagnoses = self.env['hr.hospital.diagnosis'].search([
            ('physician', 'in', self.physician_ids.ids),
            ('date_of_diagnosis', '>=', start_date),
            ('date_of_diagnosis', '<=', end_date)
        ])

        # Group diagnoses by disease
        disease_stats = {}
        for diagnosis in diagnoses:
            disease = diagnosis.disease_id
            if disease not in disease_stats:
                disease_stats[disease] = 1
            else:
                disease_stats[disease] += 1

        # Generate report data
        data = {
            'physician_ids': self.physician_ids.ids,
            'start_date': start_date,
            'end_date': end_date,
            'disease_stats': [(
                disease.id, disease.name, count
                ) for disease, count in disease_stats.items()
                ]
        }

        # Return the action to generate the report
        return self.env.ref(
            'hr_hospital.action_physician_disease_report').report_action(
            self, data=data)
