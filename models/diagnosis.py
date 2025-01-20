import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Diagnosis(models.Model):
    _name = 'hr.hospital.diagnosis'
    _description = 'Diagnosis'

    date_of_diagnosis = fields.Date(required=True)
    physician = fields.Many2one(
        comodel_name='hr.hospital.physician',
        required=True
    )
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        required=True
    )
    disease_id = fields.Many2one(
        comodel_name='hr.hospital.disease',
        required=True
    )
    treatment_recommendations = fields.Text(required=True)

    @api.constrains('treatment_recommendations')
    def _check_treatment_recommendations(self):
        for record in self:
            if not record.treatment_recommendations or not record.treatment_recommendations.strip():
                raise ValidationError('Treatment recommendations cannot be empty')
