import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Patient(models.Model):
    _name = 'hr.hospital.patient'
    _inherit = 'hr_hospital.person'
    _description = 'Patient'

    physician_ids = fields.Many2many(
        comodel_name='hr.hospital.physician',
    )

    disease_ids = fields.Many2many(
        comodel_name='hr.hospital.disease',
    )
