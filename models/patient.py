import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class Patient(models.Model):
    _name = 'hr.hospital.patient'
    _description = 'Patient'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)

    physician_ids = fields.Many2many(
        comodel_name='hr.hospital.physician',
    )

    disease_ids = fields.Many2many(
        comodel_name='hr.hospital.disease',
    )
