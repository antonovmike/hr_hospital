import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class Physician(models.Model):
    _name = 'hr.hospital.physician'
    _inherit = 'hr_hospital.person'
    _description = 'Physician'

    name = fields.Char(required=True)
    specialty = fields.Char(default='Internal Medicine')
    is_intern = fields.Boolean()
    mentor_id = fields.Many2one(
        'hr.hospital.physician',
        string='Mentor',
        domain=[('is_intern', '=', False)]
    )
    intern_ids = fields.One2many(
        'hr.hospital.physician',
        'mentor_id',
        string='Interns',
        help='List of interns under supervision'
    )
    patient_ids = fields.Many2many(
        comodel_name='hr.hospital.patient',
    )
    user_id = fields.Many2one(
        'res.users',
        string='Related User'
    )

    @api.constrains('is_intern', 'mentor_id')
    def _check_intern_mentor_constraints(self):
        for record in self:
            if record.mentor_id and record.mentor_id.is_intern:
                raise ValidationError(_(
                    'An intern cannot be assigned as a mentor'
                ))
            if not record.is_intern and record.mentor_id:
                raise ValidationError(_(
                    'Interns cannot be mentors to other physicians'
                ))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record.is_intern:
                self.env[
                    'hr.hospital.physician.schedule'
                    ].generate_slots_for_physician(record.id)
        return records

    def generate_schedule_slots(self):
        """Action to generate schedule slots for the physician."""
        self.ensure_one()
        if self.is_intern:
            raise ValidationError(_(
                "Cannot generate schedule slots for interns"))
        self.env[
            'hr.hospital.physician.schedule'].generate_slots_for_physician(
            self.id)
