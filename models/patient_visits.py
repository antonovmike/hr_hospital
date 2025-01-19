import logging

from odoo import models, fields
from odoo.exceptions import ValidationError

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

    def write(self, vals):
        """Override write to prevent modification of past visits."""
        for record in self:
            if (record.start_date_and_time and 
                    record.start_date_and_time < fields.Datetime.now()):
                restricted_fields = {'start_date_and_time', 'physisian_id'}
                if any(field in vals for field in restricted_fields):
                    raise ValidationError(
                        "Cannot modify the date/time or physician of a "
                        "visit that has already taken place."
                    )
        return super().write(vals)
