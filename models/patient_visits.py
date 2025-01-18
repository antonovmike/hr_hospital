import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class PatientVisits(models.Model):
    _name = "hr.hospital.patient.visits"
    _description = "Patient Visits"

    start_date_and_time = fields.Datetime()
    physisian_id = fields.Many2one(
        comodel_name='hr.hospital.physician',
        string='Physician',
    )
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
    )
    diagnosis_id = fields.Many2one(
        comodel_name='hr.hospital.diagnosis',
        string='Diagnosis',
    )
