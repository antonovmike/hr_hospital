import logging
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Patient(models.Model):
    _name = 'hr.hospital.patient'
    _inherit = 'hr_hospital.person'
    _description = 'Patient'

    date_of_birth = fields.Date()
    age = fields.Integer(compute='_compute_age', store=True)
    passport_details = fields.Char()
    contact_person = fields.Char()

    personal_physician = fields.Many2many(
        comodel_name='hr.hospital.physician',
    )

    disease_ids = fields.Many2many(
        comodel_name='hr.hospital.disease',
    )

    @api.depends('date_of_birth')
    def _compute_age(self):
        for rec in self:
            if rec.date_of_birth:
                rec.age = relativedelta(
                    date.today(),
                    date(rec.date_of_birth.year, rec.date_of_birth.month, rec.date_of_birth.day),
                ).years
            else:
                rec.age = False
