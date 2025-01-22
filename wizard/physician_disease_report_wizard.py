from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class PhysicianDiseaseReportWizard(models.TransientModel):
    _name = 'hr.hospital.physician.disease.report.wizard'
    _description = 'Physician Disease Report Wizard'

    physician_ids = fields.Many2many(
        'hr.hospital.physician',
        'disease_report_physician_rel',
        'wizard_id',
        'physician_id',
        string='Physicians',
        required=True
    )
    year = fields.Selection(
        selection='_get_year_selection',
        required=True,
        default=lambda self: str(fields.Date.today().year)
    )
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December')
    ], required=True,
        default=lambda self: str(fields.Date.today().month))

    disease_stats_ids = fields.One2many(
        'hr.hospital.physician.disease.report.stats',
        'wizard_id',
        string='Disease Statistics',
        readonly=True
    )

    @api.model
    def _get_year_selection(self):
        current_year = fields.Date.today().year
        return [(
            str(year), str(year)) for year in range(
                current_year - 5, current_year + 1)]

    def _prepare_stats_data(self):
        self.ensure_one()
        if not (self.physician_ids and self.year and self.month):
            return []

        # Calculate start and end dates
        start_date = date(int(self.year), int(self.month), 1)
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

        return [(0, 0, {
            'disease_id': disease.id,
            'count': count
        }) for disease, count in disease_stats.items()]

    @api.onchange('physician_ids', 'year', 'month')
    def _onchange_compute_disease_stats(self):
        self.disease_stats_ids = False  # Clear existing records
        if self.physician_ids and self.year and self.month:
            self.disease_stats_ids = self._prepare_stats_data()

    def action_generate_report(self):
        self.ensure_one()
        if not self.disease_stats_ids:
            self.disease_stats_ids = self._prepare_stats_data()

        data = {
            'physician_ids': self.physician_ids.ids,
            'start_date': date(int(self.year), int(self.month), 1),
            'end_date': date(
                int(self.year), int(self.month), 1) + relativedelta(
                    months=1, days=-1),
            'disease_stats': [(
                stat.disease_id.id, stat.disease_id.name, stat.count
                ) for stat in self.disease_stats_ids
            ]
        }

        return self.env.ref(
            'hr_hospital.action_physician_disease_report').report_action(
            self, data=data)


class PhysicianDiseaseReportStats(models.TransientModel):
    _name = 'hr.hospital.physician.disease.report.stats'
    _description = 'Disease Statistics Line'

    wizard_id = fields.Many2one(
        'hr.hospital.physician.disease.report.wizard',
        string='Wizard Reference'
    )
    disease_id = fields.Many2one(
        'hr.hospital.disease',
        string='Disease',
        required=True
    )
    count = fields.Integer(
        string='Number of Cases',
        required=True
    )
