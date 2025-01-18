import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Physician(models.Model):
    _name = 'hr.hospital.physician'
    _inherit = 'hr_hospital.person'
    _description = 'Physician'

    specialty = fields.Char(default='Internal Medicine')

    patient_ids = fields.Many2many(
        comodel_name='hr.hospital.patient',
    )
