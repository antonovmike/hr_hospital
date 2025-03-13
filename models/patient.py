import logging
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Patient(models.Model):
    _name = 'hr.hospital.patient'
    _inherit = 'hr.hospital.person'
    _description = 'Patient'

    date_of_birth = fields.Date()
    age = fields.Integer(compute='_compute_age', store=True)
    passport_details = fields.Char()
    contact_person = fields.Char()

    personal_physician = fields.Many2one(
        comodel_name='hr.hospital.physician',
    )

    disease_ids = fields.Many2many(
        comodel_name='hr.hospital.disease',
    )

    def write(self, vals):
        """Override write to track physician changes."""
        if 'personal_physician' in vals:
            self.env['hr.hospital.physician.change.history'].create({
                'date_established': fields.Datetime.now(),
                'patient_id': self.id,
                'physician_id': vals['personal_physician'],
            })
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to track initial physician assignment."""
        records = super().create(vals_list)
        for record in records:
            if record.personal_physician:
                self.env['hr.hospital.physician.change.history'].create({
                    'date_established': fields.Datetime.now(),
                    'patient_id': record.id,
                    'physician_id': record.personal_physician.id,
                })
        return records

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            if rec.date_of_birth:
                rec.age = relativedelta(
                    date.today(),
                    date(
                        rec.date_of_birth.year,
                        rec.date_of_birth.month,
                        rec.date_of_birth.day
                        ),
                ).years
            else:
                rec.age = False
