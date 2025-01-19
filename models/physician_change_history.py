import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class PhysicianChangeHistory(models.Model):
    _name = "hr.hospital.physician.change.history"
    _description = "Personal Physician Change History"
    _order = "date_established desc"

    date_established = fields.Datetime(
        string="Date Established",
        required=True,
        default=fields.Datetime.now,
    )
    patient_id = fields.Many2one(
        comodel_name='hr.hospital.patient',
        string='Patient',
        required=True,
        index=True,
    )
    physician_id = fields.Many2one(
        comodel_name='hr.hospital.physician',
        string='Physician',
        required=True,
        index=True,
    )
