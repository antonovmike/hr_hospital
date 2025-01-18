import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Diagnosis(models.Model):
    _name = 'hr.hospital.diagnosis'
    _description = 'Diagnosis'

    date_of_diagnosis = fields.Date()
    physician = fields.Many2one(
        comodel_name='hr.hospital.physician',
    )
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
    )
    disease_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
    )
    treatment_recommendations = fields.Text()
