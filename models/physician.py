import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Physician(models.Model):
    _name = 'hr.hospital.physician'
    _description = 'Physician'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    specialty = fields.Char(default='Internal Medicine')

    patient_ids = fields.Many2many(
        comodel_name='hr.hospital.patient',
    )
